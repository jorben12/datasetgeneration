# Clothing Rating & Outfit Designer

AI-ready dataset generation tool for fashion outfit compatibility prediction.

## Quick Start

### 1. Get Dataset

```bash
python organize_dataset.py
# Places your zip file's images into TrainingPictures/Tops and Bottoms
# Auto-samples 100 tops + 100 bottoms for variety
```

### 2. Rate Clothing

```bash
python clothing_rating_app.py
```

**Mode 1**: Rate individual items (5 characteristics, 0-15 scale each)
**Mode 2**: Create outfits + rate outfit harmony (5 sliders for combined looks)

### 3. Use Data for ML

```python
import pandas as pd
df = pd.read_csv('output/outfit_ratings.csv')
# 18 ML-ready columns with top/bottom/outfit characteristics + weather
```

## Files

### Python Scripts

- `clothing_rating_app.py` - Main rating UI (tkinter)
- `dataset_downloader_v3.py` - Kaggle dataset downloader
- `organize_dataset.py` - Quick zip organizer (100 tops + 100 bottoms)

### Output

- `output/clothing_ratings.csv` - Individual item ratings (6 columns)
- `output/outfit_ratings.csv` - Complete outfit data (18 columns, ML-ready)

## CSV Format

### clothing_ratings.csv

```
image, Warm-Cool, Elegant-Lively, Formal-Informal, Baggy-Loose, Feminine-Masculine
```

### outfit_ratings.csv (18 columns)

```
top_image, bottom_image,
top_warm_cool, top_elegant_lively, top_formal_informal, top_baggy_loose, top_feminine_masculine,
bottom_warm_cool, bottom_elegant_lively, bottom_formal_informal, bottom_baggy_loose, bottom_feminine_masculine,
outfit_warm_cool, outfit_elegant_lively, outfit_formal_informal, outfit_baggy_loose, outfit_feminine_masculine,
temperature, rain, cloud
```

## Workflow

1. **Download**: Get dataset from Kaggle (or use zip you have)
2. **Organize**: Run `organize_dataset.py` to sort into Tops/Bottoms
3. **Rate Items**: Use Mode 1 to rate individual pieces (~100 items, 10 min)
4. **Create Outfits**: Use Mode 2 to rate outfit combinations (~50 outfits, 20 min)
5. **Train ML**: Use outfit_ratings.csv with sklearn/TensorFlow

## Requirements

- Python 3.7+
- tkinter (Arch: `sudo pacman -S tk`)
- See requirements.txt for pip packages

## Installation

```bash
pip install -r requirements.txt
# On Arch: sudo pacman -S tk
python clothing_rating_app.py
```

## Tips

- All ratings use 0-15 scale (consistent across all features)
- Weather randomizes for each outfit
- Output CSVs append data (never overwrite)
- Mode 1 rates individual items
- Mode 2 rates complete outfit combinations
