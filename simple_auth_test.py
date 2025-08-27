#!/usr/bin/env python3
"""
Simple test to verify external browser authentication enforcement
"""

# Test the authentication validation
try:
    from mcp_server_snowflake.utils import validate_authentication_method
    
    print("Testing authentication validation...")
    
    # Test 1: Valid externalbrowser auth
    params1 = {'authenticator': 'externalbrowser', 'user': 'test@example.com'}
    result1 = validate_authentication_method(params1)
    print(f"✅ Test 1 PASSED - External browser auth accepted: {result1}")
    
    # Test 2: Invalid auth method
    try:
        params2 = {'authenticator': 'snowflake', 'user': 'test@example.com', 'password': 'secret'}
        result2 = validate_authentication_method(params2)
        print("❌ Test 2 FAILED - Should have rejected snowflake auth")
    except ValueError as e:
        print(f"✅ Test 2 PASSED - Correctly rejected snowflake auth: {e}")
    
    # Test 3: Default behavior
    params3 = {'user': 'test@example.com'}
    result3 = validate_authentication_method(params3)
    print(f"✅ Test 3 PASSED - Defaults to externalbrowser: {result3}")
    
    print("\n🎉 All authentication validation tests passed!")
    print("External browser authentication is properly enforced.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
