import torch.nn as nn
import coremltools as ct
import numpy as np
import time
import torch

channels = 256
m, n = 16, 16

class TestModel(nn.Module):
    def __init__(self):
        super(TestModel, self).__init__()
        self.action = nn.Sequential(
            nn.Conv2d(2, channels, kernel_size=3, padding=1),
            nn.Conv2d(channels, channels, kernel_size=1),
            nn.Conv2d(channels, channels, kernel_size=1),
            nn.Conv2d(channels, channels, kernel_size=1),
            nn.Conv2d(channels, channels, kernel_size=1),
            nn.Conv2d(channels, channels, kernel_size=1),
            nn.Conv2d(channels, channels, kernel_size=1),
            nn.Conv2d(channels, channels, kernel_size=1),
            nn.Conv2d(channels, channels, kernel_size=1),
            nn.Conv2d(channels, channels, kernel_size=1),
            nn.Conv2d(channels, channels, kernel_size=1),
            nn.Conv2d(channels, channels, kernel_size=1),
            nn.Conv2d(channels, channels, kernel_size=1),
            nn.Conv2d(channels, 2, kernel_size=1),
            nn.Flatten(),
            nn.LogSoftmax(dim=1),
        )

    def forward(self, x):
        return self.action(x)


def to_coreml(torch_model, batch_size, compute_units):
    torch_model = torch_model.cpu()
    torch_model.eval()
    sample = torch.rand(batch_size, 2, m, n).detach()

    traced_model = torch.jit.trace(torch_model, sample)
    return ct.convert(
        traced_model,
        inputs=[ct.TensorType(shape=sample.shape)],
        compute_units=compute_units
    )

run_for_nseconds = 30
step_target = 0.05 * run_for_nseconds

model = TestModel()
for log_batch_size in range(9, 12):
    batch_size = 2 ** log_batch_size

    sample = {'x': np.random.rand(batch_size, 2, m, n)}

    ne_model = to_coreml(model, batch_size, compute_units=ct.ComputeUnit.CPU_AND_NE)

    start = time.time()
    it = 0
    step = 100
    while True:
        for _ in range(step):
            out = ne_model.predict(sample)
        it += step
        curr = time.time()
        if curr > run_for_nseconds + start:
            break
        if curr < start + step_target:
            step *= 2

    duration = time.time() - start
    total_ranked = it * batch_size
    ms_per_sample = 1000.0 * duration / total_ranked

    print(f'{batch_size},{duration:.3f},{total_ranked},{ms_per_sample:.3f}')

