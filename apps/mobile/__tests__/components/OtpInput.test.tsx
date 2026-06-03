import { render, fireEvent } from '@testing-library/react-native';

import { OtpInput } from '@/components/auth/OtpInput';
import { ThemeProvider } from '@/theme';

function wrap(children: React.ReactNode) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

describe('OtpInput', () => {
  it('strips non-digits and clamps to length', () => {
    const onChange = jest.fn();
    const { getByLabelText } = render(wrap(<OtpInput value="" onChange={onChange} length={6} />));
    const input = getByLabelText('Código de verificación');
    fireEvent.changeText(input, 'abc12-34567');
    // Stripped to digits "1234567", clamped to 6.
    expect(onChange).toHaveBeenLastCalledWith('123456');
  });

  it('fires onComplete exactly when length is hit', () => {
    const onComplete = jest.fn();
    const onChange = jest.fn();
    const { getByLabelText } = render(
      wrap(<OtpInput value="" onChange={onChange} length={6} onComplete={onComplete} />),
    );
    const input = getByLabelText('Código de verificación');
    fireEvent.changeText(input, '12345');
    expect(onComplete).not.toHaveBeenCalled();
    fireEvent.changeText(input, '123456');
    expect(onComplete).toHaveBeenCalledWith('123456');
  });
});
