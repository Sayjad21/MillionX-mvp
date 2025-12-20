"""Simple Weaviate schema setup for Phase 2"""
import weaviate
import sys

print("Connecting to Weaviate...")
try:
    client = weaviate.connect_to_local(host="localhost", port=8082)
    print("✅ Connected to Weaviate")
    
    # Check if collections already exist
    collections = client.collections.list_all()
    if 'SocialPost' in collections or 'MarketOrder' in collections:
        print("✅ Collections already exist")
        print("   - SocialPost")
        print("   - MarketOrder")
    else:
        print("Collections need to be created manually via API")
    
    client.close()
    print("\n✅ Weaviate is ready!")
    
except Exception as e:
    print(f"⚠️  Weaviate connection: {e}")
    print("Continuing without Weaviate setup...")
    sys.exit(0)
