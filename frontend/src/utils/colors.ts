export const generateRandomColor = (): string => {
    // Generate RGB values between 0-180 instead of 0-255 to avoid light colors
    const r = Math.floor(Math.random() * 180);
    const g = Math.floor(Math.random() * 180);
    const b = Math.floor(Math.random() * 180);
    
    return `rgb(${r}, ${g}, ${b})`;
};
