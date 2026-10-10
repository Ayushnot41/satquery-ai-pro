"""Parameter-Efficient Fine-Tuning (LoRA / QLoRA) Configuration for BigEarthNet.txt VLM Adaptation.

Defines reproducible hyperparameters, target modules, precision quantization (4-bit NF4),
and evaluation checkpoints for adapting vision-language models to Sentinel-1 / Sentinel-2 data.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class BigEarthNetLoRAConfig:
    # Model specification
    base_model_name_or_path: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    adapter_name: str = "bhuvision-bigearthnet-lora-v1"
    
    # Quantization (QLoRA)
    load_in_4bit: bool = True
    bnb_4bit_compute_dtype: str = "bfloat16"
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True

    # LoRA parameters
    r: int = 64
    lora_alpha: int = 128
    lora_dropout: float = 0.05
    bias: str = "none"
    target_modules: list[str] = None  # type: ignore

    # Training settings
    learning_rate: float = 2e-4
    warmup_ratio: float = 0.03
    lr_scheduler_type: str = "cosine"
    weight_decay: float = 0.01
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_train_epochs: int = 3
    logging_steps: int = 10
    save_strategy: str = "epoch"
    evaluation_strategy: str = "steps"
    eval_steps: int = 50

    # Multi-sensor configuration
    optical_bands: list[str] = None  # type: ignore
    sar_bands: list[str] = None  # type: ignore

    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = [
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj",
            ]
        if self.optical_bands is None:
            self.optical_bands = ["B02", "B03", "B04", "B08", "B05", "B06", "B07", "B8A", "B11", "B12"]
        if self.sar_bands is None:
            self.sar_bands = ["VV", "VH"]

    def save(self, filepath: str | Path = "./pipeline/bigearthnet/lora_training_config.json") -> Path:
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)
        return p


if __name__ == "__main__":
    cfg = BigEarthNetLoRAConfig()
    out = cfg.save()
    print(f"Saved reproducible LoRA config to {out}")
