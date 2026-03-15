import torch
import csv
import os
from torch import nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

data = []
targets = []

class outfit_chooser(nn.Module):
    def __init__(self):
        super(outfit_chooser, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(13, 64),
            nn.LeakyReLU(0.075),
            nn.Linear(64, 32),
            nn.LeakyReLU(0.015),
            nn.Linear(32, 6),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.network(x)


with open("output/outfit_ratings.csv") as file:
    reader = csv.DictReader(file)

    for row in reader:
        features = [
            float(row["top_casual_formal"]), float(row["top_minimal_colorful"]), float(row["top_fitted_oversized"]), float(row["top_feminine_masculine"]), float(row["top_simple_ornate"]), float(row["bottom_casual_formal"]), float(row["bottom_minimal_colorful"]), float(row["bottom_fitted_oversized"]), float(row["bottom_feminine_masculine"]), float(row["bottom_simple_ornate"]), float(row["temperature"]), float(row["rain"]), float(row["cloud"])
            ]
        data.append(features)
        results = [
            float(row["outfit_casual_formal"]), float(row["outfit_minimal_colorful"]), float(row["outfit_fitted_oversized"]), float(row["outfit_feminine_masculine"]), float(row["outfit_simple_ornate"]), float(row["outfit_match"])
        ]
        targets.append(results)


Input_tensor = torch.tensor(data, dtype=torch.float32)
Output_tensor = torch.tensor(targets, dtype=torch.float32)

# Load and integrate user feedback data
clothing_ratings = {}
if os.path.exists("output/clothing_ratings.csv"):
    with open("output/clothing_ratings.csv") as file:
        reader = csv.DictReader(file)
        for row in reader:
            clothing_ratings[row['image']] = row

feedback_input = []
feedback_output = []
if os.path.exists("output/user_feedback.csv"):
    with open("output/user_feedback.csv") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                top = row['top']
                bottom = row['bottom']
                
                # Look up clothing ratings
                if top in clothing_ratings and bottom in clothing_ratings:
                    top_ratings = clothing_ratings[top]
                    bottom_ratings = clothing_ratings[bottom]
                    
                    # Create feature vector (values already normalized in CSV)
                    features = [
                        float(top_ratings.get("Casual-Formal", 0.5)),
                        float(top_ratings.get("Minimal-Colorful", 0.5)),
                        float(top_ratings.get("Fitted-Oversized", 0.5)),
                        float(top_ratings.get("Feminine-Masculine", 0.5)),
                        float(top_ratings.get("Simple-Ornate", 0.5)),
                        float(bottom_ratings.get("Casual-Formal", 0.5)),
                        float(bottom_ratings.get("Minimal-Colorful", 0.5)),
                        float(bottom_ratings.get("Fitted-Oversized", 0.5)),
                        float(bottom_ratings.get("Feminine-Masculine", 0.5)),
                        float(bottom_ratings.get("Simple-Ornate", 0.5)),
                        float(row['temperature']),
                        float(row['rain']),
                        float(row['cloud'])
                    ]
                    feedback = float(row['feedback'])
                    feedback_input.append(features)
                    # Use feedback value for all 6 outputs
                    feedback_output.append([feedback] * 6)
            except (KeyError, ValueError, TypeError) as e:
                print(f"Skipping feedback row due to error: {e}")
                continue

# Combine outfit ratings with user feedback
if feedback_input:
    feedback_input_tensor = torch.tensor(feedback_input, dtype=torch.float32)
    feedback_output_tensor = torch.tensor(feedback_output, dtype=torch.float32)
    Input_tensor = torch.cat([Input_tensor, feedback_input_tensor], dim=0)
    Output_tensor = torch.cat([Output_tensor, feedback_output_tensor], dim=0)
    print(f"Combined {len(data)} outfit ratings with {len(feedback_input)} user feedback samples")

indices = torch.randperm(Input_tensor.size(0))
Input_tensor = Input_tensor[indices]
Output_tensor = Output_tensor[indices]
split = int(len(Input_tensor) * 0.8)
Input_train = Input_tensor[:split]
Output_train = Output_tensor[:split]
Input_test = Input_tensor[split:]
Output_test = Output_tensor[split:]

model = outfit_chooser()
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.0005, weight_decay=0.0001)  # Lower LR, add L2 regularization

def init_weights(m):
    if isinstance(m, nn.Linear):
        torch.nn.init.xavier_uniform_(m.weight)
        m.bias.data.fill_(0.01)

model.apply(init_weights)
epochs = 500
best_test_loss = float('inf')
patience = 20
patience_counter = 0

for epoch in range(epochs):
    model.train()
    prediction = model(Input_train)

    loss = criterion(prediction, Output_train)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if epoch%10 == 0:
        model.eval()

        with torch.no_grad():
            test_preds = model(Input_test)
            test_loss = criterion(test_preds, Output_test)

            print(f"Epoch {epoch}, Train loss: {loss.item():.4f}, Test loss: {test_loss.item():.4f} ")
            
            # Early stopping: if test loss isn't improving, stop training
            if test_loss < best_test_loss:
                best_test_loss = test_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"Early stopping at epoch {epoch}. Best test loss: {best_test_loss:.4f}")
                    break

torch.save(model.state_dict(), "outfit_model.pth")


def train_from_user_feedback():
    """Train model based on user feedback from Mode 4"""
    
    # Load clothing ratings for feature lookup
    clothing_ratings = {}
    if os.path.exists("output/clothing_ratings.csv"):
        with open("output/clothing_ratings.csv") as file:
            reader = csv.DictReader(file)
            for row in reader:
                clothing_ratings[row['image']] = row
    
    # Load user feedback data
    feedback_data = []
    if os.path.exists("output/user_feedback.csv"):
        with open("output/user_feedback.csv") as file:
            reader = csv.DictReader(file)
            for row in reader:
                top = row['top']
                bottom = row['bottom']
                
                # Look up clothing ratings
                if top in clothing_ratings and bottom in clothing_ratings:
                    top_ratings = clothing_ratings[top]
                    bottom_ratings = clothing_ratings[bottom]
                    
                    # Create feature vector (values already normalized in CSV)
                    features = [
                        float(top_ratings.get("Casual-Formal", 0.5)),
                        float(top_ratings.get("Minimal-Colorful", 0.5)),
                        float(top_ratings.get("Fitted-Oversized", 0.5)),
                        float(top_ratings.get("Feminine-Masculine", 0.5)),
                        float(top_ratings.get("Simple-Ornate", 0.5)),
                        float(bottom_ratings.get("Casual-Formal", 0.5)),
                        float(bottom_ratings.get("Minimal-Colorful", 0.5)),
                        float(bottom_ratings.get("Fitted-Oversized", 0.5)),
                        float(bottom_ratings.get("Feminine-Masculine", 0.5)),
                        float(bottom_ratings.get("Simple-Ornate", 0.5)),
                        float(row['temperature']),  # Already normalized in CSV
                        float(row['rain']),  # Already normalized in CSV
                        float(row['cloud'])  # Already normalized in CSV
                    ]
                    
                    # Get target (whether user said it was good)
                    feedback = float(row['feedback'])
                    
                    feedback_data.append((features, feedback))
    
    if not feedback_data:
        print("No valid feedback data found to train on.")
        return
    
    print(f"Training on {len(feedback_data)} user feedback samples...")
    
    # Create tensors
    feedback_features = torch.tensor([f[0] for f in feedback_data], dtype=torch.float32)
    feedback_targets = torch.tensor([[f[1]] * 6 for f in feedback_data], dtype=torch.float32)  # Duplicate feedback for 6 outputs
    
    # Load existing model
    model = outfit_chooser()
    if os.path.exists("outfit_model.pth"):
        model.load_state_dict(torch.load("outfit_model.pth"))
        print("Loaded existing model for fine-tuning")
    
    # Training setup
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Train on feedback
    epochs = 200
    for epoch in range(epochs):
        model.train()
        predictions = model(feedback_features)
        loss = criterion(predictions, feedback_targets)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        if epoch % 10 == 0:
            print(f"Feedback Training Epoch {epoch}, Loss: {loss.item():.4f}")
    
    # Save updated model
    torch.save(model.state_dict(), "outfit_model.pth")
    print("Model trained and saved!")


if __name__ == "__main__":
    # Uncomment to train from user feedback instead of outfit_ratings
    train_from_user_feedback()
    pass
