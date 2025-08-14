try:
    import modal
    print("✅ Modal is available")
    print(f"Modal version: {modal.__version__}")
except ImportError as e:
    print(f"❌ Modal not available: {e}")
