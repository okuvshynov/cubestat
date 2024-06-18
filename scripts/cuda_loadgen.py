import torch
import torch.nn as nn
import torch.optim as optim
from torch.nn.parallel import DataParallel

# Check if multiple GPUs are available
if torch.cuda.device_count() < 2:
    print("This script requires at least two GPUs")
    exit()

# Set up a simple neural network model
class SimpleModel(nn.Module):
    def __init__(self):
        super(SimpleModel, self).__init__()
        self.fc = nn.Linear(1000, 1000)

    def forward(self, x):
        return self.fc(x)

# Create model and wrap it with DataParallel to utilize multiple GPUs
model = SimpleModel().cuda()
model = DataParallel(model)

# Random input data
input_data = torch.randn(64, 1000).cuda()

# Loss function and optimizer
criterion = nn.MSELoss()
optimizer = optim.SGD(model.parameters(), lr=0.001)

# Simulate a load on GPUs by running several training steps
for _ in range(100):  # Increase or decrease the number of iterations as needed
    optimizer.zero_grad()
    outputs = model(input_data)
    loss = criterion(outputs, torch.randn(64, 1000).cuda())  # Random target for demonstration
    loss.backward()
    optimizer.step()
    print(f"Loss: {loss.item()}")

print("Done simulating GPU load")
