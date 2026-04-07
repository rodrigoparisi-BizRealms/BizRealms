/**
 * Safe number formatting utility to prevent crashes on undefined/NaN values.
 * Use this instead of .toFixed() anywhere in the app.
 */
export const safeFixed = (val: any, digits: number = 2): string => {
  const num = Number(val);
  return isNaN(num) ? '0' : num.toFixed(digits);
};
