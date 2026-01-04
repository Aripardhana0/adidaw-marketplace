import models
from database import SessionLocal, engine
import random

db = SessionLocal()

# Existing assets in public/assets/ (We need to make sure they are copied there)
# We assume the following files exist in frontend/public/assets/:
# - product-shoe-1.png
# - product-shoe-2.png
# - product-shoe-3.png

IMAGES = {
    "Running": "/assets/product-men.png",      # Fallback/Generic Running
    "Soccer": "/assets/product-sports.png",     # Cleats
    "Basketball": "/assets/product-basketball.png",
    "Golf": "/assets/product-golf.png",
    "Outdoor": "/assets/product-outdoor.png",
    "Lifestyle": "/assets/product-women.png",   # Lifestyle sneakers
    "Clothing": "/assets/product-clothing.png",
    "Accessories": "/assets/product-accessories.png",
    "Collab": "/assets/product-collab.png",
    "Kids": "/assets/product-kids.png"
}

# (Category, Description keyword, Price Range, Image Key)
PRODUCT_TYPES = [
    ("Sports", "Predator Edge Cleats", "RP 2.000.000 - RP 5.000.000", "Soccer"),
    ("Sports", "X Speedportal", "RP 1.500.000 - RP 3.500.000", "Soccer"),
    ("Sports", "Copa Pure", "RP 1.000.000 - RP 2.500.000", "Soccer"),
    
    ("Sports", "Harden Vol 7", "RP 2.300.000 - RP 3.000.000", "Basketball"),
    ("Sports", "Dame 8 Extply", "RP 1.800.000 - RP 2.500.000", "Basketball"),
    ("Sports", "Trae Young 3", "RP 2.000.000 - RP 2.800.000", "Basketball"),

    ("Sports", "Ultraboost Light", "RP 2.800.000 - RP 3.300.000", "Running"),
    ("Sports", "Adizero Adios Pro", "RP 3.000.000 - RP 4.000.000", "Running"),
    ("Sports", "Galaxy 6", "RP 800.000 - RP 1.200.000", "Running"),

    ("Sports", "Terrex Free Hiker", "RP 3.000.000 - RP 4.500.000", "Outdoor"),
    ("Sports", "Terrex Soulstride", "RP 1.500.000 - RP 2.200.000", "Outdoor"),

    ("Sports", "Codechaos Golf Shoes", "RP 2.500.000 - RP 3.500.000", "Golf"),
    ("Sports", "ZG23 Golf Shoes", "RP 3.000.000 - RP 4.000.000", "Golf"),

    ("Men", "Essentials Hoodie", "RP 800.000 - RP 1.500.000", "Clothing"),
    ("Men", "Tiro Track Pants", "RP 700.000 - RP 1.200.000", "Clothing"),
    ("Men", "3-Stripes Tee", "RP 400.000 - RP 800.000", "Clothing"),
    ("Men", "Power Backpack", "RP 500.000 - RP 900.000", "Accessories"),

    ("Women", "NMD_R1", "RP 2.000.000 - RP 2.800.000", "Lifestyle"),
    ("Women", "Stan Smith", "RP 1.500.000 - RP 2.000.000", "Lifestyle"),
    ("Women", "Superstar", "RP 1.600.000 - RP 2.100.000", "Lifestyle"),
    ("Women", "Adicolor Hoodie", "RP 900.000 - RP 1.400.000", "Clothing"),
    ("Women", "Linear Duffel Bag", "RP 600.000 - RP 1.000.000", "Accessories"),

    ("Kids", "Grand Court Kids", "RP 500.000 - RP 900.000", "Kids"),
    ("Kids", "Duramo Protect", "RP 600.000 - RP 1.000.000", "Kids"),
    ("Kids", "Disney Lion King Set", "RP 800.000 - RP 1.200.000", "Clothing"), # Fallback to clothing/kids

    ("Brands", "Y-3 Kaiwa", "RP 5.000.000 - RP 8.000.000", "Collab"),
    ("Brands", "Y-3 Gazelle", "RP 4.500.000 - RP 6.000.000", "Collab"),
    ("Brands", "Humanrace Samba", "RP 2.500.000 - RP 4.000.000", "Collab"),
    ("Brands", "Ivy Park Forum", "RP 3.000.000 - RP 5.000.000", "Collab"),
    
    ("Outlet", "Runfalcon 2.0", "RP 600.000 - RP 900.000", "Running"),
    ("Outlet", "Lite Racer Adapt", "RP 700.000 - RP 1.000.000", "Running")
]

def generate_products():
    db = SessionLocal()
    
    # Clear existing products
    db.query(models.Product).delete()
    db.commit()

    products_to_create = []
    
    # Generate 120 products
    for i in range(120):
        # Pick a base type
        base_product = random.choice(PRODUCT_TYPES)
        category = base_product[0]
        name_base = base_product[1]
        price_range = base_product[2]
        image_key = base_product[3]
        
        # Randomize name slightly for variety
        suffixes = ["Pro", "Elite", "V1", "V2", "Classic", "Sport", "Original", "Limited", "Boost", "Prime"]
        name = f"Adidaw {name_base} {random.choice(suffixes)}"
        
        # Calculate random price within range
        min_p, max_p = [int(p.replace("RP ", "").replace(".", "")) for p in price_range.split(" - ")]
        price_val = random.randint(min_p, max_p)
        price_str = f"Rp {price_val:,.0f}".replace(",", ".")

        image_url = IMAGES.get(image_key, "/assets/product-men.png")

        # logic for specific sub-assignment to ensure category page population
        # e.g. if it's a Golf Shoe but assigned query category "Sports", it works for /sports.
        # But we also want correct categorization for filters if we add them later.
        # For now, sticking to the PAGE Categories: Men, Women, Kids, Sports, Brands, Outlet.
        
        # Force distribution to ensure Footer categories (Golf, Soccer etc) which redirect to /sports 
        # actually show meaningful items if searched. But current routing is by Category Column.
        # We will distribute widely.

        product = models.Product(
            name=name,
            description=f"High performance Adidaw {name} for your active lifestyle.",
            price=price_str,
            category=category,
            image=image_url,
            is_new=random.choice([True, False, False]) # 1 in 3 chance
        )
        db.add(product)
        print(f"Added: {name} ({category})")
    
    db.commit()
    print("Seeding complete: 120+ Products created!")

if __name__ == "__main__":
    generate_products()
