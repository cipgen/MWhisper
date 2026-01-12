from PIL import Image
import sys
import os

def process_icon(input_path, output_path, size=None):
    """
    Process icon: remove background and optionally resize.
    If size is None, keeps original size (High Res).
    """
    print(f"Processing {input_path} -> {os.path.basename(output_path)}...")
    try:
        img = Image.open(input_path).convert("RGBA")
        
        # Get background color from top-left pixel
        bg_color = img.getpixel((0, 0))
        
        # Create a clean transparency mask
        data = img.getdata()
        new_data = []
        
        tolerance = 30
        
        for item in data:
            # Check difference from bg color
            diff = sum(abs(c1 - c2) for c1, c2 in zip(item[:3], bg_color[:3]))
            
            if diff < tolerance:
                # Transparent
                new_data.append((0, 0, 0, 0))
            else:
                new_data.append(item)
                
        img.putdata(new_data)
        
        # Resize if needed
        if size:
            print(f"  Resizing to {size}")
            img = img.resize(size, Image.Resampling.LANCZOS)
        else:
            print(f"  Keeping original size: {img.size}")
        
        # Save
        img.save(output_path, "PNG")
        print(f"  Saved to {output_path}")
        
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    # Source high-res files (from artifacts)
    source_icons = {
        "idle": "/Users/admin/.gemini/antigravity/brain/6d7ea390-3489-4445-bd4c-976c10a8dcb7/icon_idle_1768185211142.png",
        "active": "/Users/admin/.gemini/antigravity/brain/6d7ea390-3489-4445-bd4c-976c10a8dcb7/icon_active_1768185224433.png",
        "ready": "/Users/admin/.gemini/antigravity/brain/6d7ea390-3489-4445-bd4c-976c10a8dcb7/icon_ready_1768185237192.png",
    }
    
    output_dir = "/Users/admin/Desktop/DevOps/MWhisper/assets"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Generate High-Res App Icon (1024x1024)
    # We use the 'idle' icon as the main app icon
    process_icon(source_icons["idle"], os.path.join(output_dir, "app_icon.png"), size=None)
    
    # 2. Generate Menu Bar Icons (44x44)
    process_icon(source_icons["idle"], os.path.join(output_dir, "menu_icon_idle.png"), size=(44, 44))
    process_icon(source_icons["active"], os.path.join(output_dir, "menu_icon_active.png"), size=(44, 44))
    process_icon(source_icons["ready"], os.path.join(output_dir, "menu_icon_ready.png"), size=(44, 44))
