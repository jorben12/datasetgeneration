"""
Quick Dataset Organizer
Extracts zip, organizes into Tops/Bottoms, samples 100 of each for variety
"""

import os
import shutil
import zipfile
import random
from pathlib import Path

class DatasetOrganizer:
    def __init__(self, output_base_folder="TrainingPictures"):
        self.output_base_folder = output_base_folder
        self.tops_folder = os.path.join(output_base_folder, "Tops")
        self.bottoms_folder = os.path.join(output_base_folder, "Bottoms")
        
        os.makedirs(self.tops_folder, exist_ok=True)
        os.makedirs(self.bottoms_folder, exist_ok=True)
        
        self.top_keywords = [
            'shirt', 'blouse', 't-shirt', 'tee', 'top', 'sweater', 'sweatshirt',
            'cardigan', 'tank', 'vest', 'polo',
            'crop', 'bra', 'camisole', 'tunic', 'jumper',
            'jacket', 'hoodie', 'blazer', 'coat',
        ]
        
        self.bottom_keywords = [
            'pants', 'jeans', 'shorts', 'skirt', 'leggings', 'trousers',
            'chinos', 'cargo', 'joggers', 'capris', 'culottes'
        ]
        
        self.skip_keywords = [
            'dress',
             'mantel', 'denim',
            'shoe', 'boot', 'sneaker', 'sandal', 'heel', 'loafer',
            'bag', 'purse', 'backpack', 'suitcase', 'wallet',
            'hat', 'cap', 'beanie', 'scarf', 'tie', 'belt',
            'necklace', 'bracelet', 'ring', 'earring', 'pendant', 'jewelry',
            'watch', 'glasses', 'sunglasses', 'glove', 'sock'
        ]
    
    def find_zip_file(self):
        """Find the dataset zip file in current directory"""
        for file in os.listdir('.'):
            if file.endswith('.zip') and 'apparel' in file.lower():
                return file
        
        # Also check for generic zip files
        zips = [f for f in os.listdir('.') if f.endswith('.zip')]
        if zips:
            print(f"Found zip files: {zips}")
            choice = input("Which zip file to extract? (filename): ").strip()
            if choice in zips:
                return choice
        
        return None
    
    def extract_zip(self, zip_path):
        """Extract zip file to temp folder"""
        temp_folder = "temp_extract"
        print(f"Extracting {zip_path}...")
        
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
        
        os.makedirs(temp_folder, exist_ok=True)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_folder)
            print(f"✓ Extracted to {temp_folder}")
            return temp_folder
        except Exception as e:
            print(f"✗ Error extracting: {e}")
            return None
    
    def classify_item(self, filename, full_path=""):
        """Classify if item is top or bottom"""
        name = (filename + " " + full_path).lower()
        
        # Skip excluded items
        for keyword in self.skip_keywords:
            if keyword in name:
                return None
        
        # Classify as bottom
        for keyword in self.bottom_keywords:
            if keyword in name:
                return "bottom"
        
        # Classify as top
        for keyword in self.top_keywords:
            if keyword in name:
                return "top"
        
        # Default to top for unclassified items
        return None
    
    def organize_images(self, source_folder, max_per_type=10):
        """Organize images, limiting to max_per_type each"""
        print(f"\nOrganizing images from {source_folder}...")
        
        all_tops = []
        all_bottoms = []
        skipped_count = 0
        
        # Walk through all files
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    src_path = os.path.join(root, file)
                    
                    # Classify
                    item_type = self.classify_item(file, src_path)
                    
                    if item_type is None:
                        skipped_count += 1
                        continue
                    
                    # Store with source path for later copying
                    if item_type == "bottom":
                        all_bottoms.append((file, src_path))
                    else:
                        all_tops.append((file, src_path))
        
        print(f"Found: {len(all_tops)} tops, {len(all_bottoms)} bottoms")
        print(f"Skipped: {skipped_count} accessories/shoes/etc")
        
        # Randomly sample for variety
        print(f"\nSampling {max_per_type} items from each category for variety...")
        
        if len(all_tops) > max_per_type:
            sampled_tops = random.sample(all_tops, max_per_type)
            print(f"Sampled {max_per_type} tops (from {len(all_tops)} available)")
        else:
            sampled_tops = all_tops
            print(f"Using all {len(all_tops)} tops (less than {max_per_type})")
        
        if len(all_bottoms) > max_per_type:
            sampled_bottoms = random.sample(all_bottoms, max_per_type)
            print(f"Sampled {max_per_type} bottoms (from {len(all_bottoms)} available)")
        else:
            sampled_bottoms = all_bottoms
            print(f"Using all {len(all_bottoms)} bottoms (less than {max_per_type})")
        
        # Copy sampled images
        print("\nCopying images...")
        copy_count = 0
        
        for filename, src_path in sampled_tops:
            dest_path = os.path.join(self.tops_folder, filename)
            if not os.path.exists(dest_path):
                try:
                    shutil.copy2(src_path, dest_path)
                    copy_count += 1
                except Exception as e:
                    print(f"Error copying {filename}: {e}")
        
        for filename, src_path in sampled_bottoms:
            dest_path = os.path.join(self.bottoms_folder, filename)
            if not os.path.exists(dest_path):
                try:
                    shutil.copy2(src_path, dest_path)
                    copy_count += 1
                except Exception as e:
                    print(f"Error copying {filename}: {e}")
        
        return copy_count

def main():
    print("=" * 70)
    print("DATASET QUICK ORGANIZER")
    print("=" * 70)
    
    organizer = DatasetOrganizer()
    
    # Find zip file
    zip_file = organizer.find_zip_file()
    
    if not zip_file:
        print("\n✗ No zip file found in current directory!")
        print("Please place your dataset zip file here first.")
        print("Example: apparel-images-dataset.zip")
        return
    
    print(f"\n✓ Found zip file: {zip_file}")
    
    # Extract
    temp_folder = organizer.extract_zip(zip_file)
    if not temp_folder:
        return
    
    # Organize
    try:
        image_count = organizer.organize_images(temp_folder, max_per_type=100)
        
        # Show results
        tops_count = len([f for f in os.listdir(organizer.tops_folder) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
        bottoms_count = len([f for f in os.listdir(organizer.bottoms_folder) 
                            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
        
        print(f"\n✓ Successfully organized {image_count} images!")
        print(f"\nResults:")
        print(f"  Tops: {tops_count} items")
        print(f"  Bottoms: {bottoms_count} items")
        print(f"  Total: {tops_count + bottoms_count} items ready for rating")
        
        print(f"\n✓ Ready to use! Run:")
        print(f"  python clothing_rating_app.py")
    
    finally:
        # Clean up temp folder
        if os.path.exists(temp_folder):
            print(f"\nCleaning up {temp_folder}...")
            shutil.rmtree(temp_folder)
            print("✓ Done!")

if __name__ == "__main__":
    main()
