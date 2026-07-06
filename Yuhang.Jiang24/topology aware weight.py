import time
import psutil
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from scipy.spatial.distance import directed_hausdorff
from sklearn.metrics import accuracy_score
from monai.networks.nets import UNet
import matplotlib.pyplot as plt


# ===================== 拓扑特征提取器 =====================
class TopologyFeatureExtractor:
    def __init__(self, n_neighbors=15, rips_max_dim=2):
        self.n_neighbors = n_neighbors
        self.rips_max_dim = rips_max_dim

    def get_full_topo_vector(self, mask):
        """输入二值分割掩码，输出6维拓扑特征向量"""
        mask = (mask > 0.5).astype(np.uint8)
        if np.sum(mask) < 10:
            return np.zeros(6, dtype=np.float32)

        # 特征1：全局清晰度（类间方差比）
        ig = self._global_clarity(mask)
        # 特征2：局部清晰度（分块方差均值）
        il = self._local_clarity(mask)
        # 特征3：平均聚类系数
        avg_clustering = self._avg_clustering(mask)
        # 特征4：轮廓系数
        silhouette = self._silhouette_score(mask)
        # 特征5：孤立点比例
        isolated_ratio = self._isolated_ratio(mask)
        # 特征6：孔洞指数（归一化Betti1数）
        hole_index = self._hole_index(mask)

        return np.array([ig, il, avg_clustering, silhouette, isolated_ratio, hole_index], dtype=np.float32)

    def _global_clarity(self, mask):
        coords = np.argwhere(mask == 1)
        if len(coords) < 2:
            return 0.0
        var_total = np.var(coords, axis=0).sum()
        return min(1.0, var_total / 10000.0)

    def _local_clarity(self, mask, grid=16):
        h, w = mask.shape
        block_h, block_w = h // grid, w // grid
        vars_list = []
        for i in range(grid):
            for j in range(grid):
                block = mask[i * block_h:(i + 1) * block_h, j * block_w:(j + 1) * block_w]
                vars_list.append(np.var(block))
        return min(1.0, np.mean(vars_list) * 100)

    def _avg_clustering(self, mask):
        from sklearn.neighbors import kneighbors_graph
        coords = np.argwhere(mask == 1)
        if len(coords) < self.n_neighbors + 1:
            return 0.0
        sample_idx = np.random.choice(len(coords), min(500, len(coords)), replace=False)
        coords_sample = coords[sample_idx]
        try:
            import networkx as nx
            A = kneighbors_graph(coords_sample, self.n_neighbors, mode='connectivity')
            G = nx.from_scipy_sparse_array(A)
            return nx.average_clustering(G)
        except:
            return 0.5

    def _silhouette_score(self, mask):
        from sklearn.metrics import silhouette_score
        from sklearn.cluster import KMeans
        coords = np.argwhere(mask == 1)
        if len(coords) < 10:
            return 0.0
        sample_idx = np.random.choice(len(coords), min(300, len(coords)), replace=False)
        coords_sample = coords[sample_idx]
        try:
            kmeans = KMeans(n_clusters=min(3, len(coords_sample)), n_init=10, random_state=42)
            labels = kmeans.fit_predict(coords_sample)
            if len(set(labels)) < 2:
                return 0.5
            return (silhouette_score(coords_sample, labels) + 1) / 2
        except:
            return 0.5

    def _isolated_ratio(self, mask):
        from scipy.ndimage import label
        labeled, num_features = label(mask)
        if num_features == 0:
            return 0.0
        sizes = [np.sum(labeled == i) for i in range(1, num_features + 1)]
        small_clusters = sum(1 for s in sizes if s < 5)
        return min(1.0, small_clusters / num_features)

    def _hole_index(self, mask):
        from scipy.ndimage import binary_fill_holes
        filled = binary_fill_holes(mask)
        hole_pixels = np.sum(filled) - np.sum(mask)
        total_pixels = np.sum(filled) + 1e-8
        return min(1.0, hole_pixels / total_pixels)


# ===================== 拓扑约束分割模型（MONAI UNet骨干） =====================
class TopologyConstrainedModel(nn.Module):
    def __init__(self, in_channels=1, out_channels=1, feature_dim=64):
        super().__init__()

        # MONAI官方UNet骨干（替换手写简化版）
        self.backbone = UNet(
            spatial_dims=2,
            in_channels=in_channels,
            out_channels=feature_dim,
            channels=(16, 32, 64, 128),
            strides=(2, 2, 2),
            num_res_units=2,
        )

        # 分割输出头
        self.seg_head = nn.Conv2d(feature_dim, out_channels, 1)

        # 拓扑特征预测分支
        self.topo_head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(feature_dim, 6)
        )

        # 动态权重网络（拓扑特征 → 损失权重）
        self.weight_net = nn.Sequential(
            nn.Linear(6, 32),
            nn.ReLU(),
            nn.Linear(32, 2),
            nn.Softmax(dim=1)
        )

    def forward(self, x, subtype_labels=None, gt_topo=None, gt_mask=None, is_train=True):
        # 编码+解码（MONAI UNet）
        features = self.backbone(x)

        # 分割掩码
        pred_mask = torch.sigmoid(self.seg_head(features))

        # 拓扑特征预测
        pred_topo = self.topo_head(features)

        outputs = {"pred_mask": pred_mask, "pred_topo": pred_topo}

        # 训练阶段计算损失
        if is_train and gt_topo is not None and gt_mask is not None:
            # Dice损失
            dice_loss = 1 - (2 * (pred_mask * gt_mask).sum() + 1e-8) / (pred_mask.sum() + gt_mask.sum() + 1e-8)
            # 拓扑特征MSE损失
            topo_loss = nn.MSELoss()(pred_topo, gt_topo)
            # 动态权重融合
            weights = self.weight_net(gt_topo)
            total_loss = weights[0][0] * dice_loss + weights[0][1] * topo_loss

            outputs["loss"] = total_loss
            outputs["dice_loss"] = dice_loss
            outputs["topo_loss"] = topo_loss

        return outputs


# ===================== 模拟医学数据集（支持多尺寸） =====================
class MockMedicalDataset(Dataset):
    def __init__(self, num_samples=30, img_size_list=[128, 256, 512], feature_dim=64):
        self.num_samples = num_samples
        self.img_size_list = img_size_list
        self.feature_dim = feature_dim
        self.topo_extractor = TopologyFeatureExtractor()

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        img_size = np.random.choice(self.img_size_list)
        # 生成模拟图像
        image = np.random.randn(1, img_size, img_size).astype(np.float32)
        # 生成模拟掩码（带拓扑缺陷）
        mask = np.random.randint(0, 2, (img_size, img_size)).astype(np.float32)
        # 计算拓扑金标准
        topo_gt = self.topo_extractor.get_full_topo_vector(mask)
        mask = np.expand_dims(mask, axis=0)
        # 模拟亚型标签
        subtype_labels = np.random.randint(0, 3)

        return {
            "image": image,
            "mask": mask,
            "topo_gt": topo_gt,
            "subtype_labels": subtype_labels
        }


# ===================== 训练函数 =====================
def train_model(epochs=5, batch_size=2, device="cuda"):
    train_dataset = MockMedicalDataset(num_samples=100, img_size_list=[128, 256, 384, 512])
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=lambda batch: {
            "image": torch.tensor(np.stack([item["image"] for item in batch])),
            "mask": torch.tensor(np.stack([item["mask"] for item in batch])),
            "topo_gt": torch.tensor(np.stack([item["topo_gt"] for item in batch])),
            "subtype_labels": [item["subtype_labels"] for item in batch]
        }
    )

    model = TopologyConstrainedModel(feature_dim=64).to(device)
    optimizer = optim.Adam(model.parameters(), lr=1e-4)

    model.train()
    for epoch in range(epochs):
        total_loss = 0.0
        for batch in train_loader:
            image = batch["image"].to(device)
            mask = batch["mask"].to(device)
            topo_gt = batch["topo_gt"].to(device)

            optimizer.zero_grad()
            outputs = model(
                x=image,
                subtype_labels=batch["subtype_labels"],
                gt_topo=topo_gt,
                gt_mask=mask,
                is_train=True
            )
            loss = outputs["loss"]
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        print(f"Epoch {epoch + 1}/{epochs}, Loss: {total_loss / len(train_loader):.6f}")

    torch.save(model.state_dict(), "topology_constrained_model.pth")
    return model


# ===================== 评估函数 =====================
def evaluate_model(model, test_loader, device="cuda"):
    model.eval()
    metrics = {
        "dice_scores": [], "iou_scores": [], "hd95_scores": [], "pixel_acc": [],
        "topo_mse": [], "hole_index_error": [], "isolated_ratio_error": [],
        "img_sizes": [], "infer_times": [], "gpu_mem_usage": [],
    }

    with torch.no_grad():
        for batch in test_loader:
            for i in range(len(batch["image"])):
                image = batch["image"][i].unsqueeze(0).to(device)
                mask = batch["mask"][i].unsqueeze(0).to(device)
                topo_gt = batch["topo_gt"][i:i + 1].to(device)
                subtype_labels = [batch["subtype_labels"][i]]
                h, w = image.shape[2], image.shape[3]
                metrics["img_sizes"].append((h, w))

                start_time = time.time()
                outputs = model(
                    x=image,
                    subtype_labels=subtype_labels,
                    gt_topo=topo_gt,
                    gt_mask=mask,
                    is_train=False
                )
                infer_time = time.time() - start_time
                metrics["infer_times"].append(infer_time)

                if device == "cuda":
                    mem_used = torch.cuda.memory_allocated(device) / (1024 ** 2)
                    metrics["gpu_mem_usage"].append(mem_used)
                    torch.cuda.empty_cache()

                pred_mask = outputs["pred_mask"].cpu().numpy().squeeze()
                gt_mask = mask.cpu().numpy().squeeze()
                pred_mask_bin = (pred_mask > 0.5).astype(np.uint8)
                gt_mask_bin = (gt_mask > 0.5).astype(np.uint8)

                intersection = np.sum(pred_mask_bin * gt_mask_bin)
                dice = 2 * intersection / (np.sum(pred_mask_bin) + np.sum(gt_mask_bin) + 1e-8)
                metrics["dice_scores"].append(dice)

                union = np.sum(np.logical_or(pred_mask_bin, gt_mask_bin))
                iou = intersection / (union + 1e-8)
                metrics["iou_scores"].append(iou)

                if np.sum(pred_mask_bin) > 0 and np.sum(gt_mask_bin) > 0:
                    pred_coords = np.argwhere(pred_mask_bin == 1)
                    gt_coords = np.argwhere(gt_mask_bin == 1)
                    hd1 = directed_hausdorff(pred_coords, gt_coords)[0]
                    hd2 = directed_hausdorff(gt_coords, pred_coords)[0]
                    hd95 = np.percentile([hd1, hd2], 95)
                else:
                    hd95 = 0.0
                metrics["hd95_scores"].append(hd95)

                pixel_acc = accuracy_score(gt_mask_bin.flatten(), pred_mask_bin.flatten())
                metrics["pixel_acc"].append(pixel_acc)

                pred_topo = outputs["pred_topo"].cpu().numpy().squeeze()
                gt_topo_np = topo_gt.cpu().numpy().squeeze()

                topo_mse = np.mean((pred_topo - gt_topo_np) ** 2)
                metrics["topo_mse"].append(topo_mse)
                metrics["hole_index_error"].append(abs(pred_topo[5] - gt_topo_np[5]))
                metrics["isolated_ratio_error"].append(abs(pred_topo[4] - gt_topo_np[4]))

    eval_results = {
        "dice_mean": np.mean(metrics["dice_scores"]),
        "dice_std": np.std(metrics["dice_scores"]),
        "iou_mean": np.mean(metrics["iou_scores"]),
        "iou_std": np.std(metrics["iou_scores"]),
        "hd95_mean": np.mean(metrics["hd95_scores"]),
        "hd95_std": np.std(metrics["hd95_scores"]),
        "pixel_acc_mean": np.mean(metrics["pixel_acc"]),
        "topo_mse_mean": np.mean(metrics["topo_mse"]),
        "hole_error_mean": np.mean(metrics["hole_index_error"]),
        "isolated_error_mean": np.mean(metrics["isolated_ratio_error"]),
        "avg_infer_time": np.mean(metrics["infer_times"]),
        "infer_time_std": np.std(metrics["infer_times"]),
        "avg_gpu_mem": np.mean(metrics["gpu_mem_usage"]) if metrics["gpu_mem_usage"] else 0,
        "size_metrics": {
            "128x128_dice": np.mean(
                [d for d, s in zip(metrics["dice_scores"], metrics["img_sizes"]) if s == (128, 128)]),
            "256x256_dice": np.mean(
                [d for d, s in zip(metrics["dice_scores"], metrics["img_sizes"]) if s == (256, 256)]),
            "512x512_dice": np.mean(
                [d for d, s in zip(metrics["dice_scores"], metrics["img_sizes"]) if s == (512, 512)]),
        }
    }

    print("=" * 50)
    print("模型性能评估报告（MONAI UNet骨干）")
    print("=" * 50)
    print(f"【基础分割性能】")
    print(f"  Dice系数：{eval_results['dice_mean']:.4f} ± {eval_results['dice_std']:.4f}")
    print(f"  IoU：{eval_results['iou_mean']:.4f} ± {eval_results['iou_std']:.4f}")
    print(f"  HD95：{eval_results['hd95_mean']:.2f} ± {eval_results['hd95_std']:.2f}")
    print(f"  像素准确率：{eval_results['pixel_acc_mean']:.4f}")
    print(f"\n【拓扑特征有效性】")
    print(f"  拓扑特征MSE：{eval_results['topo_mse_mean']:.6f}")
    print(f"  孔洞指数误差：{eval_results['hole_error_mean']:.4f}")
    print(f"  孤立点比例误差：{eval_results['isolated_error_mean']:.4f}")
    print(f"\n【尺寸适配性】")
    print(f"  平均推理耗时：{eval_results['avg_infer_time']:.4f}s (±{eval_results['infer_time_std']:.4f}s)")
    print(f"  平均GPU显存占用：{eval_results['avg_gpu_mem']:.2f}MB")
    print("=" * 50)

    return eval_results, metrics


# ===================== 部署推理函数 =====================
def deploy_inference(model_path, img_np, device="cuda"):
    model = TopologyConstrainedModel(feature_dim=64).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.eval()

    if len(img_np.shape) == 2:
        img_tensor = torch.tensor(img_np).unsqueeze(0).unsqueeze(0).to(device).float()
    else:
        img_tensor = torch.tensor(img_np).unsqueeze(0).to(device).float()

    with torch.no_grad():
        outputs = model(x=img_tensor, is_train=False)

    pred_topo = outputs["pred_topo"].cpu().numpy().squeeze()
    pred_mask = outputs["pred_mask"].cpu().numpy().squeeze()
    topo_score = 1 - np.mean(pred_topo)
    mask_score = np.mean(pred_mask > 0.5)
    final_score = (topo_score + mask_score) / 2

    return {
        "输出掩码尺寸": pred_mask.shape,
        "预测拓扑特征": pred_topo.tolist(),
        "最终特征质量分": final_score
    }


# ===================== 主入口 =====================
if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"使用设备：{device}")

    # Step1：训练模型
    print("\n=== 开始训练（MONAI UNet骨干 + 拓扑约束） ===")
    trained_model = train_model(epochs=3, batch_size=2, device=device)

    # Step2：评估模型
    print("\n=== 开始评估 ===")
    test_dataset = MockMedicalDataset(num_samples=20, img_size_list=[128, 256, 384, 512])
    test_loader = DataLoader(
        test_dataset,
        batch_size=2,
        shuffle=False,
        collate_fn=lambda batch: {
            "image": torch.tensor(np.stack([item["image"] for item in batch])),
            "mask": torch.tensor(np.stack([item["mask"] for item in batch])),
            "topo_gt": torch.tensor(np.stack([item["topo_gt"] for item in batch])),
            "subtype_labels": [item["subtype_labels"] for item in batch]
        }
    )
    eval_results, raw_metrics = evaluate_model(trained_model, test_loader, device=device)

    # Step3：部署测试
    print("\n=== 部署推理测试（任意尺寸） ===")
    test_img_128 = np.random.randn(128, 128).astype(np.float32)
    result_128 = deploy_inference("topology_constrained_model.pth", test_img_128, device=device)
    print(f"128x128 输出尺寸：{result_128['输出掩码尺寸']}，质量分：{result_128['最终特征质量分']:.3f}")

    test_img_512 = np.random.randn(512, 512).astype(np.float32)
    result_512 = deploy_inference("topology_constrained_model.pth", test_img_512, device=device)
    print(f"512x512 输出尺寸：{result_512['输出掩码尺寸']}，质量分：{result_512['最终特征质量分']:.3f}")

    print("\n✅ 完整流程运行完成")