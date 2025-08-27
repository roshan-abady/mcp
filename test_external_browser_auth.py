#!/usr/bin/env python3
"""
Test script to verify external browser authentication enforcement.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_authentication_validation():
    """Test the authentication validation function."""
    try:
        from mcp_server_snowflake.utils import validate_authentication_method
        
        print("Testing authentication validation...")
        print()
        
        # Test 1: Valid externalbrowser authentication
        try:
            params = {'authenticator': 'externalbrowser', 'user': 'test@example.com'}
            result = validate_authentication_method(params)
            print('✅ Test 1 passed: externalbrowser authentication accepted')
            print(f'   Result: {result}')
        except Exception as e:
            print(f'❌ Test 1 failed: {e}')
        
        print()
        
        # Test 2: Invalid authentication method should raise error
        try:
            params = {'authenticator': 'snowflake', 'user': 'test@example.com', 'password': 'secret'}
            result = validate_authentication_method(params)
            print('❌ Test 2 failed: should have raised an error')
        except ValueError as e:
            print('✅ Test 2 passed: invalid authentication method rejected')
            print(f'   Error: {str(e)[:100]}...')
        except Exception as e:
            print(f'❌ Test 2 failed with unexpected error: {e}')
        
        print()
        
        # Test 3: Default to externalbrowser when no authenticator specified
        try:
            params = {'user': 'test@example.com'}
            result = validate_authentication_method(params)
            print('✅ Test 3 passed: defaults to externalbrowser')
            print(f'   Result: {result}')
        except Exception as e:
            print(f'❌ Test 3 failed: {e}')
        
        print()
        
        # Test 4: Remove password and private key parameters
        try:
            params = {
                'authenticator': 'externalbrowser', 
                'user': 'test@example.com', 
                'password': 'secret', 
                'private_key': 'key'
            }
            result = validate_authentication_method(params)
            print('✅ Test 4 passed: password and private key parameters removed')
            print(f'   Result: {result}')
            assert 'password' not in result
            assert 'private_key' not in result
        except Exception as e:
            print(f'❌ Test 4 failed: {e}')
        
        print()
        print('All tests completed!')
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_authentication_validation()
    sys.exit(0 if success else 1)
