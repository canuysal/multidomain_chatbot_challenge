#!/usr/bin/env python3
"""
Database bootstrap script to create tables and populate with sample data
"""

import json
import sys
import os
from decimal import Decimal
from typing import List, Dict, Any

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, create_tables, reset_database
from app.models.product import Product


def load_sample_products() -> List[Dict[Any, Any]]:
    """Load sample products from JSON file"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, "sample_products.json")

        with open(json_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"❌ Error: sample_products.json not found at {json_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in sample_products.json: {e}")
        return []


def create_sample_products(db_session, products_data: List[Dict[Any, Any]]) -> int:
    """Create sample products in the database"""
    created_count = 0

    for product_data in products_data:
        try:
            # Convert price string to Decimal
            price_decimal = Decimal(str(product_data['price']))

            # Create product instance
            product = Product(
                name=product_data['name'],
                category=product_data['category'],
                description=product_data.get('description'),
                price=price_decimal,
                brand=product_data.get('brand'),
                in_stock=product_data.get('in_stock', True),
                stock_quantity=product_data.get('stock_quantity', 0)
            )

            db_session.add(product)
            created_count += 1
            print(f"✅ Added: {product.name}")

        except Exception as e:
            print(f"❌ Error adding product '{product_data.get('name', 'Unknown')}': {e}")

    return created_count


def bootstrap_database(reset: bool = False):
    """Bootstrap the database with sample data"""
    print("🚀 Starting database bootstrap...")

    try:
        # Create or reset tables
        if reset:
            print("🔄 Resetting database (dropping and recreating tables)...")
            reset_database()
        else:
            print("📋 Creating database tables...")
            create_tables()

        # Load sample data
        print("📂 Loading sample products...")
        sample_products = load_sample_products()

        if not sample_products:
            print("❌ No sample products loaded. Exiting.")
            return False

        # Create database session
        db = SessionLocal()

        try:
            # Check if products already exist (only if not resetting)
            if not reset:
                existing_count = db.query(Product).count()
                if existing_count > 0:
                    print(f"⚠️  Database already contains {existing_count} products.")
                    overwrite = input("Do you want to add more products anyway? (y/N): ").lower().strip()
                    if overwrite != 'y':
                        print("🛑 Bootstrap cancelled.")
                        return True

            # Create sample products
            print(f"🛍️  Creating {len(sample_products)} sample products...")
            created_count = create_sample_products(db, sample_products)

            # Commit changes
            db.commit()

            # Verify creation
            total_products = db.query(Product).count()

            print(f"\n✅ Bootstrap completed successfully!")
            print(f"📊 Created {created_count} new products")
            print(f"📦 Total products in database: {total_products}")

            # Show sample of created products
            print("\n🔍 Sample products created:")
            sample_products_db = db.query(Product).limit(5).all()
            for product in sample_products_db:
                status = "✅ In Stock" if product.in_stock and product.stock_quantity > 0 else "❌ Out of Stock"
                print(f"  • {product.name} (${product.price}) - {status}")

            if total_products > 5:
                print(f"  ... and {total_products - 5} more products")

            return True

        except Exception as e:
            db.rollback()
            print(f"❌ Error during database operations: {e}")
            return False

        finally:
            db.close()

    except Exception as e:
        print(f"❌ Fatal error during bootstrap: {e}")
        return False


def show_database_status():
    """Show current database status"""
    try:
        db = SessionLocal()
        try:
            total_products = db.query(Product).count()
            in_stock_products = db.query(Product).filter(
                Product.in_stock == True,
                Product.stock_quantity > 0
            ).count()

            categories = db.query(Product.category).distinct().all()
            category_list = [cat[0] for cat in categories]

            print(f"\n📊 Database Status:")
            print(f"  📦 Total products: {total_products}")
            print(f"  ✅ In stock: {in_stock_products}")
            print(f"  ❌ Out of stock: {total_products - in_stock_products}")
            print(f"  🏷️  Categories: {', '.join(category_list)}")

        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error checking database status: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Bootstrap the chatbot database")
    parser.add_argument("--reset", action="store_true", help="Reset database (drop and recreate tables)")
    parser.add_argument("--status", action="store_true", help="Show database status only")

    args = parser.parse_args()

    if args.status:
        show_database_status()
    else:
        success = bootstrap_database(reset=args.reset)
        if success:
            show_database_status()
            print("\n🎉 Database bootstrap completed successfully!")
        else:
            print("\n💥 Database bootstrap failed!")
            sys.exit(1)