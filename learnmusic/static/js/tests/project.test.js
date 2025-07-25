/**
 * Tests for cache functionality in project.js
 * @jest-environment jsdom
 */

// Import the cache module from project.js
// Using a relative path from the test file to project.js
const project = require('../project.js');
const cache = project.cache;

// Mock localStorage for testing
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn(key => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn(key => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    })
  };
})();

// Set up global mocks
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

describe('Cache Module', () => {
  // Reset mocks and localStorage before each test
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.clear();
  });

  describe('checkPermission', () => {
    test('returns false when consent is not stored', () => {
      expect(cache.checkPermission()).toBe(false);
    });

    test('returns true when consent is stored as true', () => {
      localStorageMock.setItem('tootology-consent', 'true');
      expect(cache.checkPermission()).toBe(true);
    });

    test('returns false when consent is stored as false', () => {
      localStorageMock.setItem('tootology-consent', 'false');
      expect(cache.checkPermission()).toBe(false);
    });
  });

  describe('permissionGiven', () => {
    test('sets consent to true in localStorage', () => {
      cache.permissionGiven();
      expect(localStorageMock.setItem).toHaveBeenCalledWith('tootology-consent', 'true');
    });

    test('returns true on success', () => {
      expect(cache.permissionGiven()).toBe(true);
    });
  });

  describe('permissionRemoved', () => {
    test('removes consent from localStorage', () => {
      localStorageMock.setItem('tootology-consent', 'true');
      cache.permissionRemoved();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('tootology-consent');
    });

    test('returns true on success', () => {
      expect(cache.permissionRemoved()).toBe(true);
    });
  });

  describe('save', () => {
    test('does not save data when consent is not given', () => {
      // Ensure consent is not given
      localStorageMock.setItem('tootology-consent', 'false');
      cache.checkPermission();

      const result = cache.save('test-key', { data: 'test-data' });

      expect(result).toBe(false);
      expect(localStorageMock.setItem).not.toHaveBeenCalledWith('test-key', expect.any(String));
    });

    test('saves data when consent is given', () => {
      // Give consent
      cache.permissionGiven();

      const testData = { data: 'test-data' };
      const result = cache.save('test-key', testData);

      expect(result).toBe(true);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('test-key', JSON.stringify(testData));
    });

    test('handles errors during save', () => {
      // Give consent
      cache.permissionGiven();

      // Mock setItem to throw an error
      localStorageMock.setItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      const result = cache.save('test-key', { data: 'test-data' });

      expect(result).toBe(false);
    });
  });

  describe('get', () => {
    test('returns null when consent is not given', () => {
      // Ensure consent is not given
      localStorageMock.setItem('tootology-consent', 'false');
      cache.checkPermission();

      // Add data to localStorage directly (bypassing consent check)
      localStorageMock.setItem('test-key', JSON.stringify({ data: 'test-data' }));

      const result = cache.get('test-key');

      expect(result).toBe(null);
    });

    test('retrieves data when consent is given', () => {
      // Give consent
      cache.permissionGiven();

      // Add data to localStorage
      const testData = { data: 'test-data' };
      localStorageMock.setItem('test-key', JSON.stringify(testData));

      const result = cache.get('test-key');

      expect(result).toEqual(testData);
    });

    test('returns null for non-existent keys', () => {
      // Give consent
      cache.permissionGiven();

      const result = cache.get('non-existent-key');

      expect(result).toBe(null);
    });

    test('handles invalid JSON data', () => {
      // Give consent
      cache.permissionGiven();

      // Add invalid JSON data to localStorage
      localStorageMock.setItem('test-key', 'invalid-json');

      const result = cache.get('test-key');

      expect(result).toBe(null);
    });

    test('handles errors during retrieval', () => {
      // Give consent
      cache.permissionGiven();

      // Mock getItem to throw an error
      localStorageMock.getItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      const result = cache.get('test-key');

      expect(result).toBe(null);
    });

    test('sets and returns default value for non-existent keys when provided', () => {
      // Give consent
      cache.permissionGiven();

      const defaultValue = { default: 'value' };
      const result = cache.get('non-existent-key', defaultValue);

      expect(result).toEqual(defaultValue);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('non-existent-key', JSON.stringify(defaultValue));
    });

    test('does not set default value when consent is not given', () => {
      // Ensure consent is not given
      localStorageMock.setItem('tootology-consent', 'false');
      cache.checkPermission();

      const defaultValue = { default: 'value' };
      const result = cache.get('non-existent-key', defaultValue);

      expect(result).toBe(null);
      expect(localStorageMock.setItem).not.toHaveBeenCalledWith('non-existent-key', expect.any(String));
    });
  });

  describe('remove', () => {
    test('does not remove data when consent is not given', () => {
      // Ensure consent is not given
      localStorageMock.setItem('tootology-consent', 'false');
      cache.checkPermission();

      // Add data to localStorage directly (bypassing consent check)
      localStorageMock.setItem('test-key', JSON.stringify({ data: 'test-data' }));

      const result = cache.remove('test-key');

      expect(result).toBe(false);
      expect(localStorageMock.removeItem).not.toHaveBeenCalledWith('test-key');
    });

    test('removes data when consent is given', () => {
      // Give consent
      cache.permissionGiven();

      // Add data to localStorage
      localStorageMock.setItem('test-key', JSON.stringify({ data: 'test-data' }));

      const result = cache.remove('test-key');

      expect(result).toBe(true);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('test-key');
    });

    test('handles errors during removal', () => {
      // Give consent
      cache.permissionGiven();

      // Mock removeItem to throw an error
      localStorageMock.removeItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      const result = cache.remove('test-key');

      expect(result).toBe(false);
    });
  });

  describe('canStore', () => {
    test('returns true when localStorage is available', () => {
      // The test environment has localStorage available
      const result = cache._testing.canStore();
      expect(result).toBe(true);
    });

    test('returns false when localStorage is not available', () => {
      // Mock the absence of localStorage
      const originalLocalStorage = window.localStorage;
      delete window.localStorage;

      const result = cache._testing.canStore();

      // Restore localStorage
      window.localStorage = originalLocalStorage;

      expect(result).toBe(false);
    });
  });
});
