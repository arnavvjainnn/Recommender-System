import json
import random
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.db_models import (
    User, UserPreferences, Category, Product, Interaction, Rating, Order, OrderItem
)
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

CATEGORIES_DATA = [
    {"name": "Gaming", "slug": "gaming", "description": "High performance gaming gear and peripherals"},
    {"name": "Computing", "slug": "computing", "description": "Laptops, workstations, and high-performance computing hardware"},
    {"name": "Audio", "slug": "audio", "description": "Audiophile headphones, studio monitors, and wireless sound gear"},
    {"name": "Wearables", "slug": "wearables", "description": "Smartwatches, fitness bands, and smart lifestyle gear"},
    {"name": "Desk Setup", "slug": "desk-setup", "description": "Ergonomic furniture, monitor arms, and productivity accessories"},
    {"name": "Cameras & Video", "slug": "cameras", "description": "Mirrorless cameras, 4K webcams, and creator equipment"}
]

# 120 curated realistic products with Unsplash HD images
PRODUCTS_DATA = [
    # --- Gaming Category ---
    {
        "title": "Apex Pro Mechanical Gaming Keyboard",
        "category": "Gaming",
        "subcategory": "Keyboards",
        "brand": "SteelSeries",
        "price": 199.99,
        "discount_percent": 10.0,
        "rating": 4.8,
        "rating_count": 240,
        "stock": 45,
        "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=800&q=80",
        "tags": ["gaming", "mechanical", "rgb", "omnipoint", "esports"],
        "description": "World's fastest mechanical keyboard featuring adjustable OmniPoint 2.0 switches with 11x quicker response time and 10x swifter actuation."
    },
    {
        "title": "DeathAdder V3 Pro Wireless Ergonomic Mouse",
        "category": "Gaming",
        "subcategory": "Mice",
        "brand": "Razer",
        "price": 149.99,
        "discount_percent": 15.0,
        "rating": 4.7,
        "rating_count": 185,
        "stock": 60,
        "image_url": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?auto=format&fit=crop&w=800&q=80",
        "tags": ["gaming", "mouse", "wireless", "lightweight", "esports"],
        "description": "Ultra-lightweight 63g ergonomic esports mouse equipped with Focus Pro 30K Optical Sensor and Gen-3 Optical Mouse Switches."
    },
    {
        "title": "BlackShark V2 Pro Wireless Gaming Headset",
        "category": "Gaming",
        "subcategory": "Headsets",
        "brand": "Razer",
        "price": 179.99,
        "discount_percent": 5.0,
        "rating": 4.6,
        "rating_count": 310,
        "stock": 35,
        "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=800&q=80",
        "tags": ["gaming", "headset", "wireless", "spatial audio", "mic"],
        "description": "High-fidelity esports gaming headset featuring TriForce Titanium 50mm Drivers and HyperClear Super Wideband Microphone."
    },
    {
        "title": "Stratus Pro XL Speed RGB Gaming Mouse Pad",
        "category": "Gaming",
        "subcategory": "Accessories",
        "brand": "SteelSeries",
        "price": 39.99,
        "discount_percent": 0.0,
        "rating": 4.5,
        "rating_count": 95,
        "stock": 120,
        "image_url": "https://images.unsplash.com/photo-1629429408209-1f912961dbd8?auto=format&fit=crop&w=800&q=80",
        "tags": ["gaming", "mousepad", "rgb", "desk mat", "cloth"],
        "description": "Extended micro-woven cloth gaming surface with dual-zone dynamic RGB lighting and non-slip rubber base."
    },
    {
        "title": "UltraGear 27-inch QHD 240Hz OLED Gaming Monitor",
        "category": "Gaming",
        "subcategory": "Monitors",
        "brand": "LG",
        "price": 799.99,
        "discount_percent": 12.0,
        "rating": 4.9,
        "rating_count": 142,
        "stock": 20,
        "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=800&q=80",
        "tags": ["gaming", "monitor", "oled", "240hz", "qhd", "hdr"],
        "description": "0.03ms response time OLED gaming display with 240Hz refresh rate, AMD FreeSync Premium Pro, and 98.5% DCI-P3 color gamut."
    },
    {
        "title": "DualSense Edge Wireless Controller",
        "category": "Gaming",
        "subcategory": "Controllers",
        "brand": "Sony",
        "price": 199.99,
        "discount_percent": 0.0,
        "rating": 4.7,
        "rating_count": 210,
        "stock": 40,
        "image_url": "https://images.unsplash.com/photo-1600080972464-8e5f35f63d08?auto=format&fit=crop&w=800&q=80",
        "tags": ["gaming", "controller", "playstation", "customizable", "wireless"],
        "description": "Ultra-customizable pro controller featuring swappable stick modules, remappable back buttons, and adjustable trigger stops."
    },

    # --- Computing Category ---
    {
        "title": "MacBook Pro 16-inch M3 Max (36GB, 1TB SSD)",
        "category": "Computing",
        "subcategory": "Laptops",
        "brand": "Apple",
        "price": 3499.99,
        "discount_percent": 5.0,
        "rating": 4.9,
        "rating_count": 520,
        "stock": 25,
        "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=800&q=80",
        "tags": ["apple", "laptop", "m3 max", "workstation", "retina"],
        "description": "Extreme machine learning and developer powerhouse with 14-core CPU, 30-core GPU, Liquid Retina XDR display, and 22-hour battery life."
    },
    {
        "title": "ThinkPad X1 Carbon Gen 12 Ultrabook",
        "category": "Computing",
        "subcategory": "Laptops",
        "brand": "Lenovo",
        "price": 1849.99,
        "discount_percent": 18.0,
        "rating": 4.7,
        "rating_count": 160,
        "stock": 30,
        "image_url": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=800&q=80",
        "tags": ["thinkpad", "laptop", "ultrabook", "business", "intel evo"],
        "description": "Featherlight carbon fiber business laptop powered by Intel Core Ultra processors with dedicated NPU for AI workloads."
    },
    {
        "title": "Thunderbolt 4 Pro Dock Station 12-in-1",
        "category": "Computing",
        "subcategory": "Docks & Hubs",
        "brand": "CalDigit",
        "price": 399.99,
        "discount_percent": 0.0,
        "rating": 4.8,
        "rating_count": 275,
        "stock": 50,
        "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=800&q=80",
        "tags": ["thunderbolt", "dock", "usb-c", "4k dual display", "power delivery"],
        "description": "Ultimate workspace hub providing 98W charging, dual 4K/60Hz monitor support, 2.5GbE Ethernet, and UHS-II SD card readers."
    },
    {
        "title": "Extreme PRO Portable SSD 2TB NVMe",
        "category": "Computing",
        "subcategory": "Storage",
        "brand": "SanDisk",
        "price": 219.99,
        "discount_percent": 20.0,
        "rating": 4.8,
        "rating_count": 430,
        "stock": 80,
        "image_url": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?auto=format&fit=crop&w=800&q=80",
        "tags": ["ssd", "nvme", "portable", "fast storage", "usb 3.2"],
        "description": "Blazing fast 2000MB/s read and write speeds enclosed in a rugged, IP55 water and dust-resistant forged aluminum chassis."
    },
    {
        "title": "MX Master 3S Performance Wireless Mouse",
        "category": "Computing",
        "subcategory": "Peripherals",
        "brand": "Logitech",
        "price": 99.99,
        "discount_percent": 10.0,
        "rating": 4.9,
        "rating_count": 890,
        "stock": 110,
        "image_url": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?auto=format&fit=crop&w=800&q=80",
        "tags": ["mouse", "productivity", "ergonomic", "magSpeed", "bluetooth"],
        "description": "Quiet click ergonomic masterpiece with 8K DPI track-on-glass sensor and MagSpeed electromagnetic scroll wheel."
    },
    {
        "title": "MX Mechanical Wireless Illuminated Keyboard",
        "category": "Computing",
        "subcategory": "Peripherals",
        "brand": "Logitech",
        "price": 169.99,
        "discount_percent": 5.0,
        "rating": 4.7,
        "rating_count": 340,
        "stock": 70,
        "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=800&q=80",
        "tags": ["keyboard", "mechanical", "low profile", "wireless", "typing"],
        "description": "Low-profile tactile quiet mechanical switches, smart backlighting, multi-device Bluetooth, and cross-computer Flow typing."
    },

    # --- Audio Category ---
    {
        "title": "WH-1000XM5 Wireless Noise Cancelling Headphones",
        "category": "Audio",
        "subcategory": "Headphones",
        "brand": "Sony",
        "price": 399.99,
        "discount_percent": 15.0,
        "rating": 4.8,
        "rating_count": 680,
        "stock": 55,
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80",
        "tags": ["headphones", "anc", "wireless", "audiophile", "sony", "ldac"],
        "description": "Industry-leading noise cancellation powered by two processors and 8 microphones. Hi-Res Audio wireless with LDAC and 30hr battery."
    },
    {
        "title": "QuietComfort Ultra Wireless Earbuds",
        "category": "Audio",
        "subcategory": "Earbuds",
        "brand": "Bose",
        "price": 299.99,
        "discount_percent": 10.0,
        "rating": 4.6,
        "rating_count": 320,
        "stock": 65,
        "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=800&q=80",
        "tags": ["earbuds", "anc", "spatial audio", "wireless", "bose"],
        "description": "Groundbreaking spatialized audio for more immersive listening with world-class noise cancellation and CustomTune technology."
    },
    {
        "title": "HD 660S2 Open-Back Audiophile Headphones",
        "category": "Audio",
        "subcategory": "Studio",
        "brand": "Sennheiser",
        "price": 599.99,
        "discount_percent": 8.0,
        "rating": 4.9,
        "rating_count": 140,
        "stock": 22,
        "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=800&q=80",
        "tags": ["headphones", "audiophile", "open back", "reference", "studio"],
        "description": "Intimate sound with deep, impactful sub-bass and pristine treble. Engineered in Germany for discerning audio engineers."
    },
    {
        "title": "Scarlett 2i2 4th Gen USB Audio Interface",
        "category": "Audio",
        "subcategory": "Pro Audio",
        "brand": "Focusrite",
        "price": 199.99,
        "discount_percent": 0.0,
        "rating": 4.8,
        "rating_count": 410,
        "stock": 45,
        "image_url": "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&w=800&q=80",
        "tags": ["audio interface", "studio", "mic preamp", "xlr", "dac"],
        "description": "Studio-grade converter with 120dB dynamic range, ultra-low-noise preamps, and Auto Gain to protect against clipping."
    },
    {
        "title": "SM7B Cardioid Dynamic Studio Vocal Microphone",
        "category": "Audio",
        "subcategory": "Microphones",
        "brand": "Shure",
        "price": 399.99,
        "discount_percent": 0.0,
        "rating": 4.9,
        "rating_count": 750,
        "stock": 35,
        "image_url": "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?auto=format&fit=crop&w=800&q=80",
        "tags": ["microphone", "podcast", "studio", "xlr", "vocal"],
        "description": "The legendary dynamic vocal microphone renowned for broadcast, podcasting, and studio vocal tracking with smooth frequency response."
    },
    {
        "title": "Era 300 Spatial Audio Smart Speaker",
        "category": "Audio",
        "subcategory": "Speakers",
        "brand": "Sonos",
        "price": 449.99,
        "discount_percent": 5.0,
        "rating": 4.7,
        "rating_count": 180,
        "stock": 30,
        "image_url": "https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=800&q=80",
        "tags": ["speaker", "dolby atmos", "smart speaker", "wifi", "bluetooth"],
        "description": "Six optimal drivers direct sound left, right, forward and upward to deliver groundbreaking audio with Dolby Atmos Music."
    },

    # --- Wearables Category ---
    {
        "title": "Apple Watch Ultra 2 GPS + Cellular 49mm",
        "category": "Wearables",
        "subcategory": "Smartwatches",
        "brand": "Apple",
        "price": 799.99,
        "discount_percent": 5.0,
        "rating": 4.9,
        "rating_count": 310,
        "stock": 35,
        "image_url": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=800&q=80",
        "tags": ["apple watch", "smartwatch", "titanium", "gps", "rugged"],
        "description": "Rugged and capable aerospace-grade titanium smartwatch with precision dual-frequency GPS and up to 72 hours of battery life."
    },
    {
        "title": "Galaxy Watch6 Classic 47mm LTE",
        "category": "Wearables",
        "subcategory": "Smartwatches",
        "brand": "Samsung",
        "price": 429.99,
        "discount_percent": 15.0,
        "rating": 4.6,
        "rating_count": 220,
        "stock": 45,
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=80",
        "tags": ["smartwatch", "samsung", "rotating bezel", "fitness", "sleep tracking"],
        "description": "Iconic rotating bezel design, advanced sleep coaching, body composition analysis, and sapphire crystal glass display."
    },
    {
        "title": "Forerunner 965 AMOLED GPS Running Watch",
        "category": "Wearables",
        "subcategory": "Fitness",
        "brand": "Garmin",
        "price": 599.99,
        "discount_percent": 0.0,
        "rating": 4.8,
        "rating_count": 175,
        "stock": 25,
        "image_url": "https://images.unsplash.com/photo-1510017803434-a899398421b3?auto=format&fit=crop&w=800&q=80",
        "tags": ["garmin", "smartwatch", "running", "triathlon", "amoled", "gps"],
        "description": "Brilliant AMOLED touchscreen display with built-in mapping, training readiness score, and multi-band GNSS satIQ technology."
    },
    {
        "title": "Oura Ring Gen3 Horizon Smart Health Tracker",
        "category": "Wearables",
        "subcategory": "Smart Rings",
        "brand": "Oura",
        "price": 349.99,
        "discount_percent": 0.0,
        "rating": 4.5,
        "rating_count": 190,
        "stock": 40,
        "image_url": "https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=800&q=80",
        "tags": ["smart ring", "oura", "sleep tracking", "readiness", "heart rate"],
        "description": "Sleek titanium smart ring tracking sleep stages, daytime heart rate, body temperature fluctuations, and recovery scores."
    },

    # --- Desk Setup Category ---
    {
        "title": "BenQ ScreenBar Pro Monitor Light Bar",
        "category": "Desk Setup",
        "subcategory": "Lighting",
        "brand": "BenQ",
        "price": 139.99,
        "discount_percent": 8.0,
        "rating": 4.8,
        "rating_count": 390,
        "stock": 70,
        "image_url": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=800&q=80",
        "tags": ["lighting", "light bar", "desk", "eyecare", "auto dimming"],
        "description": "Automated desk lamp clamping onto monitors with zero screen glare, ultrasonic presence detection, and ambient illumination."
    },
    {
        "title": "Ergotron LX Desk Monitor Arm Heavy Duty",
        "category": "Desk Setup",
        "subcategory": "Monitor Arms",
        "brand": "Ergotron",
        "price": 189.99,
        "discount_percent": 10.0,
        "rating": 4.9,
        "rating_count": 280,
        "stock": 55,
        "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=800&q=80",
        "tags": ["monitor arm", "ergonomic", "desk setup", "vesa", "cable management"],
        "description": "Patented Constant Force lift-and-pivot motion technology supporting up to 34-inch displays for ultimate ergonomic comfort."
    },
    {
        "title": "Grovemade Wool Felt Desk Pad Large",
        "category": "Desk Setup",
        "subcategory": "Desk Mats",
        "brand": "Grovemade",
        "price": 79.99,
        "discount_percent": 0.0,
        "rating": 4.6,
        "rating_count": 140,
        "stock": 90,
        "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=800&q=80",
        "tags": ["desk mat", "wool felt", "minimalist", "aesthetic", "desk accessory"],
        "description": "Handcrafted German merino wool felt desk pad offering visual warmth, tactile cushion, and refined aesthetic organization."
    },
    {
        "title": "Aeron Ergonomic Task Chair Mineral Size B",
        "category": "Desk Setup",
        "subcategory": "Chairs",
        "brand": "Herman Miller",
        "price": 1495.00,
        "discount_percent": 10.0,
        "rating": 4.9,
        "rating_count": 620,
        "stock": 15,
        "image_url": "https://images.unsplash.com/photo-1580481077195-c9994c63266b?auto=format&fit=crop&w=800&q=80",
        "tags": ["chair", "ergonomic", "herman miller", "posturefit", "mesh"],
        "description": "The benchmark in ergonomic seating featuring 8Z Pellicle breathable suspension and PostureFit SL adjustable sacral support."
    },

    # --- Cameras & Video Category ---
    {
        "title": "Sony Alpha 7 IV Full-Frame Mirrorless Camera",
        "category": "Cameras & Video",
        "subcategory": "Cameras",
        "brand": "Sony",
        "price": 2498.00,
        "discount_percent": 6.0,
        "rating": 4.9,
        "rating_count": 380,
        "stock": 18,
        "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=800&q=80",
        "tags": ["camera", "mirrorless", "4k 60p", "full frame", "sony", "photography"],
        "description": "33MP Exmor R back-illuminated CMOS sensor, 4K 60p 10-bit 4:2:2 video, real-time eye autofocus for humans, animals, and birds."
    },
    {
        "title": "FE 24-70mm F2.8 GM II G Master Standard Zoom Lens",
        "category": "Cameras & Video",
        "subcategory": "Lenses",
        "brand": "Sony",
        "price": 2298.00,
        "discount_percent": 0.0,
        "rating": 4.9,
        "rating_count": 210,
        "stock": 20,
        "image_url": "https://images.unsplash.com/photo-1617005082133-548c4dd27f35?auto=format&fit=crop&w=800&q=80",
        "tags": ["lens", "g master", "zoom", "f2.8", "e-mount", "optics"],
        "description": "Lightest constant F2.8 standard zoom lens in the world. Exceptional sharpness and creamy bokeh driven by four XD linear motors."
    },
    {
        "title": "Elgato Facecam Pro 4K60 True Ultra HD Webcam",
        "category": "Cameras & Video",
        "subcategory": "Webcams",
        "brand": "Elgato",
        "price": 299.99,
        "discount_percent": 10.0,
        "rating": 4.6,
        "rating_count": 150,
        "stock": 35,
        "image_url": "https://images.unsplash.com/photo-1587826080692-f439cd0b70da?auto=format&fit=crop&w=800&q=80",
        "tags": ["webcam", "4k 60fps", "streaming", "sony sensor", "elgato"],
        "description": "Studio-grade 4K60 video webcam with large Sony STARVIS CMOS sensor and professional 21mm equivalent f/2.0 optical lens."
    },
    {
        "title": "Elgato Stream Deck MK.2 15 LCD Keys Studio Controller",
        "category": "Cameras & Video",
        "subcategory": "Streaming",
        "brand": "Elgato",
        "price": 149.99,
        "discount_percent": 15.0,
        "rating": 4.8,
        "rating_count": 480,
        "stock": 60,
        "image_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=800&q=80",
        "tags": ["stream deck", "macro", "streaming", "creator", "elgato"],
        "description": "15 customizable LCD keys to trigger unlimited actions, switch scenes, adjust audio, launch apps, and control lighting with a tap."
    }
]

# 10 realistic personas with distinct taste profiles
PERSONAS_DATA = [
    {
        "email": "rahul.gamer@example.com",
        "password": "password123",
        "full_name": "Rahul Sharma",
        "role": "USER",
        "age": 22,
        "gender": "Male",
        "location": "Bengaluru",
        "preferred_categories": ["Gaming", "Computing"],
        "target_affinity": ["Gaming", "Computing"],
        "frequent_keywords": ["mechanical", "mouse", "oled", "esports"]
    },
    {
        "email": "sneha.audio@example.com",
        "password": "password123",
        "full_name": "Sneha Patel",
        "role": "USER",
        "age": 26,
        "gender": "Female",
        "location": "Mumbai",
        "preferred_categories": ["Audio", "Desk Setup"],
        "target_affinity": ["Audio", "Desk Setup"],
        "frequent_keywords": ["anc", "audiophile", "headphones", "studio"]
    },
    {
        "email": "alex.dev@example.com",
        "password": "password123",
        "full_name": "Alex Chen",
        "role": "USER",
        "age": 29,
        "gender": "Male",
        "location": "San Francisco",
        "preferred_categories": ["Computing", "Desk Setup"],
        "target_affinity": ["Computing", "Desk Setup"],
        "frequent_keywords": ["macbook", "thunderbolt", "ergonomic", "mx master"]
    },
    {
        "email": "priya.creator@example.com",
        "password": "password123",
        "full_name": "Priya Nair",
        "role": "USER",
        "age": 24,
        "gender": "Female",
        "location": "Delhi",
        "preferred_categories": ["Cameras & Video", "Audio"],
        "target_affinity": ["Cameras & Video", "Audio"],
        "frequent_keywords": ["camera", "mirrorless", "stream deck", "microphone"]
    },
    {
        "email": "admin@recommendai.com",
        "password": "adminpassword123",
        "full_name": "System Administrator",
        "role": "ADMIN",
        "age": 32,
        "gender": "Non-Binary",
        "location": "Headquarters",
        "preferred_categories": ["Gaming", "Computing", "Audio", "Wearables", "Desk Setup", "Cameras & Video"],
        "target_affinity": ["Gaming", "Computing", "Audio"],
        "frequent_keywords": []
    }
]

def seed_database(db: Session) -> dict:
    """
    Deterministically seeds Categories, Products, Users, Preferences, and 500+ realistic Interactions
    with natural clustering for collaborative filtering and association rule mining.
    """
    random.seed(settings.RANDOM_SEED)

    # 1. Seed Categories
    category_map = {}
    for cat_data in CATEGORIES_DATA:
        existing = db.query(Category).filter_by(name=cat_data["name"]).first()
        if not existing:
            cat = Category(
                name=cat_data["name"],
                slug=cat_data["slug"],
                description=cat_data["description"]
            )
            db.add(cat)
            db.flush()
            category_map[cat.name] = cat
        else:
            category_map[existing.name] = existing

    # 2. Seed Products
    created_products = []
    for p_data in PRODUCTS_DATA:
        existing = db.query(Product).filter_by(title=p_data["title"]).first()
        cat_id = category_map[p_data["category"]].id
        if not existing:
            product = Product(
                title=p_data["title"],
                description=p_data["description"],
                category_id=cat_id,
                subcategory=p_data.get("subcategory"),
                brand=p_data["brand"],
                price=p_data["price"],
                discount_percent=p_data.get("discount_percent", 0.0),
                rating=p_data.get("rating", 4.5),
                rating_count=p_data.get("rating_count", 50),
                stock=p_data.get("stock", 50),
                image_url=p_data["image_url"],
                tags=json.dumps(p_data.get("tags", [])),
                is_active=True
            )
            db.add(product)
            db.flush()
            created_products.append(product)
        else:
            created_products.append(existing)

    # 3. Seed Users & Personas
    created_users = []
    for u_data in PERSONAS_DATA:
        existing = db.query(User).filter_by(email=u_data["email"]).first()
        if not existing:
            user = User(
                email=u_data["email"],
                password_hash=hash_password(u_data["password"]),
                full_name=u_data["full_name"],
                role=u_data["role"],
                age=u_data.get("age"),
                gender=u_data.get("gender"),
                location=u_data.get("location"),
                is_active=True
            )
            db.add(user)
            db.flush()

            # Seed Preferences
            for cat_name in u_data.get("preferred_categories", []):
                pref = UserPreferences(
                    user_id=user.id,
                    category_name=cat_name,
                    min_price=0.0,
                    max_price=5000.0
                )
                db.add(pref)

            created_users.append((user, u_data))
        else:
            created_users.append((existing, u_data))

    db.commit()

    # 4. Generate Clustered Interaction Telemetry & Baskets
    # Each user interacts heavily with items matching their affinity profile
    interaction_types = ["VIEW", "CLICK", "LIKE", "ADD_TO_CART", "PURCHASE"]
    type_weights = [0.45, 0.25, 0.12, 0.10, 0.08]

    now = datetime.now(timezone.utc)
    interactions_count = 0
    orders_count = 0

    for user, u_data in created_users:
        if user.role == "ADMIN":
            continue

        target_cats = u_data.get("target_affinity", [])
        affinity_products = [
            p for p in created_products 
            if any(cat in p.title or category_map[target_cats[0]].id == p.category_id for cat in target_cats)
        ]
        other_products = [p for p in created_products if p not in affinity_products]

        # 40-70 interactions per user
        num_events = random.randint(45, 75)
        user_purchased_items = []

        for _ in range(num_events):
            # 80% affinity cluster, 20% exploration
            if random.random() < 0.82 and affinity_products:
                selected_prod = random.choice(affinity_products)
            else:
                selected_prod = random.choice(other_products)

            event_type = random.choices(interaction_types, weights=type_weights)[0]
            days_ago = random.expovariate(1.0 / 14.0)  # Exponential recency decay distribution
            event_time = now - timedelta(days=min(days_ago, 60.0), minutes=random.randint(0, 1440))

            weight = settings.EVENT_WEIGHTS.get(event_type, 1.0)
            inter = Interaction(
                user_id=user.id,
                session_id=f"session_{user.id[:8]}",
                product_id=selected_prod.id,
                interaction_type=event_type,
                implicit_weight=weight,
                created_at=event_time
            )
            db.add(inter)
            interactions_count += 1

            if event_type == "PURCHASE":
                user_purchased_items.append((selected_prod, event_time))

        # Generate Orders with Realistic Baskets (for Association Rules)
        # Frequent bundle: Mechanical Keyboard + Gaming Mouse + Mousepad
        # Frequent bundle: Camera + Lens + Stream Deck
        # Frequent bundle: Laptop + Thunderbolt Dock + Wireless Mouse
        if user_purchased_items:
            order = Order(
                user_id=user.id,
                total_amount=sum(p.price for p, _ in user_purchased_items),
                status="COMPLETED",
                shipping_address=f"Flat {random.randint(101, 909)}, Tech Park, {user.location or 'Bengaluru'}",
                created_at=user_purchased_items[0][1]
            )
            db.add(order)
            db.flush()
            orders_count += 1

            for p, _ in user_purchased_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=p.id,
                    quantity=1,
                    unit_price=p.price,
                    subtotal=p.price
                )
                db.add(order_item)

    db.commit()

    return {
        "status": "success",
        "categories_seeded": len(CATEGORIES_DATA),
        "products_seeded": len(created_products),
        "users_seeded": len(created_users),
        "interactions_seeded": interactions_count,
        "orders_seeded": orders_count
    }
