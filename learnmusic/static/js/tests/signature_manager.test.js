/**
 * Tests for signature_manager.js
 */

// We will set up globals BEFORE requiring the module so it can read window.progress_data

// Keep original Math to restore if needed
const originalMath = global.Math;

// Utility to load a fresh copy of the module each test
function freshRequire() {
  jest.resetModules();
  return require('../../../../notes/templates/js/signature_manager.js');
}

describe('signature_manager', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Ensure deterministic shuffling: use 0.999 so Fisher–Yates picks j=i (no swap)
    const mockMath = Object.create(global.Math);
    mockMath.random = jest.fn(() => 0.999);
    global.Math = mockMath;

    // Provide signatures for the queue source
    global.window = {
      progress_data: {
        signatures: {
          vexflow: ['sigA', 'sigB', 'sigC']
        }
      }
    };
  });

  afterEach(() => {
    global.Math = originalMath;
    delete global.window;
  });

  test('add_signature attaches signature and keeps same signature for first 6 uses, then switches', () => {
    const signature_manager = freshRequire();

    // First 6 calls should use first signature ('sigA')
    for (let i = 1; i <= 6; i++) {
      const note = { note: 'C', octave: '4', alter: '0' };
      const res = signature_manager.add_signature(note);
      expect(res).toBe(note); // same object reference
      expect(res.signature).toBe('sigA');
    }

    // 7th call should rotate to 'sigB'
    const next = signature_manager.add_signature({ note: 'D', octave: '4', alter: '0' });
    expect(next.signature).toBe('sigB');
  });

  test('queue replenishes after exhausting all signatures', () => {
    const signature_manager = freshRequire();

    // We have 3 signatures and rotation count is 6.
    // After 18 calls (3 * 6) we should have used sigA, sigB, sigC completely.
    const used = [];
    for (let i = 1; i <= 18; i++) {
      const res = signature_manager.add_signature({ n: i });
      used.push(res.signature);
    }

    // First 6 are sigA, next 6 sigB, next 6 sigC
    expect(used.slice(0, 6).every(s => s === 'sigA')).toBe(true);
    expect(used.slice(6, 12).every(s => s === 'sigB')).toBe(true);
    expect(used.slice(12, 18).every(s => s === 'sigC')).toBe(true);

    // Next call should replenish and start again from sigA (deterministic order)
    const afterReplenish = signature_manager.add_signature({});
    expect(afterReplenish.signature).toBe('sigA');
  });

  test('add_signature preserves other note properties and returns same object', () => {
    const signature_manager = freshRequire();
    const original = { note: 'E', octave: '5', alter: '1', extra: 'data' };
    const result = signature_manager.add_signature(original);

    // Same reference
    expect(result).toBe(original);

    // Signature added
    expect(result.signature).toBeDefined();

    // Other props preserved
    expect(result.note).toBe('E');
    expect(result.octave).toBe('5');
    expect(result.alter).toBe('1');
    expect(result.extra).toBe('data');
  });
});
