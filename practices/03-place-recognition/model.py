"""Small CPU-only adapter for OPR ResNet18 + GeM (NCLT weights).

Backbone code is vendored unchanged from OPR; see third_party and SOURCES.md.
GeM and single-image forward follow OPR. No training and no GPU dependencies.
"""
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from torch import nn
import torch.nn.functional as F
from third_party.opr_resnet import ResNet18FPNFeatureExtractor


class GeM(nn.Module):
    def __init__(self):
        super().__init__()
        self.p = nn.Parameter(torch.ones(1) * 3)

    def forward(self, x):
        return F.avg_pool2d(x.clamp(min=1e-6).pow(self.p),
                            (x.size(-2), x.size(-1))).pow(1.0 / self.p).flatten(1)


class PlaceModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = ResNet18FPNFeatureExtractor(pretrained=False)
        self.head = GeM()

    def forward(self, image):
        return self.head(self.backbone(image))


def load_model(weights, threads=4):
    torch.set_num_threads(threads)
    model = PlaceModel().to('cpu')
    model.load_state_dict(torch.load(weights, map_location='cpu', weights_only=True), strict=True)
    model.eval()
    assert next(model.parameters()).device.type == 'cpu'
    return model


def preprocess(path):
    # Explicit educational resolution, same for database and query.
    with Image.open(path) as image:
        arr = np.asarray(image.convert('RGB').resize((320, 192), Image.Resampling.BILINEAR), dtype=np.float32) / 255
    arr = (arr - np.array([.485, .456, .406], dtype=np.float32)) / np.array([.229, .224, .225], dtype=np.float32)
    return torch.from_numpy(arr.transpose(2, 0, 1).copy()).unsqueeze(0)


@torch.inference_mode()
def describe(model, path):
    vector = model(preprocess(path)).numpy()[0]
    norm = np.linalg.norm(vector)
    if not np.isfinite(vector).all() or norm < 1e-12:
        raise ValueError('Invalid descriptor')
    return vector / norm
