import * as SecureStore from 'expo-secure-store';

import { secureTokens } from '@/auth/secureStorage';

describe('secureTokens', () => {
  beforeEach(() => {
    (SecureStore as unknown as { __reset: () => void }).__reset();
    secureTokens.__resetForTests();
  });

  it('saves both tokens', async () => {
    await secureTokens.save({ access: 'A', refresh: 'R' });
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
      'layapa.auth.access',
      'A',
      expect.any(Object),
    );
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
      'layapa.auth.refresh',
      'R',
      expect.any(Object),
    );
  });

  it('loads both tokens together', async () => {
    await secureTokens.save({ access: 'A', refresh: 'R' });
    const loaded = await secureTokens.load();
    expect(loaded).toEqual({ access: 'A', refresh: 'R' });
  });

  it('returns null when only one is present', async () => {
    await SecureStore.setItemAsync('layapa.auth.access', 'A', {});
    const loaded = await secureTokens.load();
    expect(loaded).toBeNull();
  });

  it('clear wipes both', async () => {
    await secureTokens.save({ access: 'A', refresh: 'R' });
    await secureTokens.clear();
    expect(await secureTokens.load()).toBeNull();
  });
});
