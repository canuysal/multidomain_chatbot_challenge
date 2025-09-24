from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.core.database import SessionLocal
from app.models.product import Product
from decimal import Decimal


class ProductTool:
    """Tool for searching products in the database"""

    def __init__(self):
        pass

    def find_products(self, query: str) -> str:
        """
        Search for products in the database by name, description, category, or brand

        Args:
            query (str): Search query for product name, description, category, or brand

        Returns:
            str: Formatted product search results or error message
        """
        try:
            if not query or not query.strip():
                return "Please provide a search term for products."

            query = query.strip().lower()

            # Get database session
            db = SessionLocal()

            try:
                # Search products using case-insensitive matching
                search_filter = or_(
                    Product.name.ilike(f"%{query}%"),
                    Product.description.ilike(f"%{query}%"),
                    Product.category.ilike(f"%{query}%"),
                    Product.brand.ilike(f"%{query}%")
                )

                products = db.query(Product).filter(search_filter).limit(10).all()

                if not products:
                    return f"No products found matching '{query}'. Try searching with different keywords."

                return self._format_product_results(products, query)

            finally:
                db.close()

        except Exception as e:
            return f"An error occurred while searching for products: {str(e)}"

    def get_product_by_id(self, product_id: int) -> str:
        """
        Get detailed information about a specific product by ID

        Args:
            product_id (int): Product ID to search for

        Returns:
            str: Formatted product details or error message
        """
        try:
            db = SessionLocal()

            try:
                product = db.query(Product).filter(Product.id == product_id).first()

                if not product:
                    return f"No product found with ID {product_id}."

                return self._format_single_product(product)

            finally:
                db.close()

        except Exception as e:
            return f"An error occurred while retrieving product details: {str(e)}"

    def get_products_by_category(self, category: str) -> str:
        """
        Get all products in a specific category

        Args:
            category (str): Product category to search for

        Returns:
            str: Formatted products in category or error message
        """
        try:
            if not category or not category.strip():
                return "Please provide a valid category name."

            category = category.strip()

            db = SessionLocal()

            try:
                products = db.query(Product).filter(
                    Product.category.ilike(f"%{category}%")
                ).limit(15).all()

                if not products:
                    return f"No products found in category '{category}'."

                return self._format_product_results(products, f"category '{category}'")

            finally:
                db.close()

        except Exception as e:
            return f"An error occurred while searching by category: {str(e)}"

    def get_products_in_stock(self) -> str:
        """
        Get all products that are currently in stock

        Returns:
            str: Formatted in-stock products or error message
        """
        try:
            db = SessionLocal()

            try:
                products = db.query(Product).filter(
                    and_(Product.in_stock == True, Product.stock_quantity > 0)
                ).limit(15).all()

                if not products:
                    return "No products are currently in stock."

                return self._format_product_results(products, "in stock")

            finally:
                db.close()

        except Exception as e:
            return f"An error occurred while retrieving in-stock products: {str(e)}"

    def _format_product_results(self, products: List[Product], search_term: str) -> str:
        """
        Format multiple product results into a readable format

        Args:
            products (List[Product]): List of products to format
            search_term (str): Original search term

        Returns:
            str: Formatted product results
        """
        try:
            response = f"🛍️ **Products found for '{search_term}' ({len(products)} results)**\n\n"

            for product in products:
                stock_status = "✅ In Stock" if product.in_stock and product.stock_quantity > 0 else "❌ Out of Stock"

                response += f"**{product.name}**\n"
                response += f"🏷️ *Category*: {product.category}"

                if product.brand:
                    response += f" | 🏢 *Brand*: {product.brand}"

                response += f"\n💰 *Price*: ${product.price}"
                response += f" | {stock_status}"

                if product.in_stock and product.stock_quantity > 0:
                    response += f" ({product.stock_quantity} available)"

                response += f"\n"

                if product.description:
                    # Limit description length
                    desc = product.description
                    if len(desc) > 100:
                        desc = desc[:97] + "..."
                    response += f"📝 *Description*: {desc}\n"

                response += f"🆔 *Product ID*: {product.id}\n\n"

            # Add summary
            in_stock_count = sum(1 for p in products if p.in_stock and p.stock_quantity > 0)
            response += f"📊 **Summary**: {len(products)} products found, {in_stock_count} in stock"

            return response.strip()

        except Exception as e:
            return f"Found products but couldn't format them properly: {str(e)}"

    def _format_single_product(self, product: Product) -> str:
        """
        Format a single product into detailed readable format

        Args:
            product (Product): Product to format

        Returns:
            str: Formatted product details
        """
        try:
            stock_status = "✅ In Stock" if product.in_stock and product.stock_quantity > 0 else "❌ Out of Stock"

            response = f"🛍️ **{product.name}**\n\n"
            response += f"🏷️ **Category**: {product.category}\n"

            if product.brand:
                response += f"🏢 **Brand**: {product.brand}\n"

            response += f"💰 **Price**: ${product.price}\n"
            response += f"📦 **Stock Status**: {stock_status}"

            if product.in_stock and product.stock_quantity > 0:
                response += f" ({product.stock_quantity} available)"

            response += f"\n🆔 **Product ID**: {product.id}\n"

            if product.description:
                response += f"\n📝 **Description**:\n{product.description}\n"

            if product.created_at:
                response += f"\n📅 **Added**: {product.created_at.strftime('%Y-%m-%d')}"

            return response.strip()

        except Exception as e:
            return f"Found product but couldn't format it properly: {str(e)}"


# Create global instance for use in OpenAI service
product_tool = ProductTool()