import React, { useEffect, useRef, useState } from 'react';
import { Animated, Text, TextStyle, View } from 'react-native';

interface AnimatedNumberProps {
  value: number;
  formatter?: (val: number) => string;
  style?: TextStyle;
  duration?: number;
}

export default function AnimatedNumber({ value, formatter, style, duration = 600 }: AnimatedNumberProps) {
  const [displayValue, setDisplayValue] = useState(value);
  const animatedVal = useRef(new Animated.Value(value)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const prevValue = useRef(value);

  useEffect(() => {
    if (value !== prevValue.current) {
      // Animate the number change
      const startVal = prevValue.current;
      prevValue.current = value;

      // Scale pop effect
      Animated.sequence([
        Animated.timing(scaleAnim, { toValue: 1.15, duration: 150, useNativeDriver: true }),
        Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 20, bounciness: 8 }),
      ]).start();

      // Count up/down animation
      const steps = 20;
      const stepDuration = duration / steps;
      const diff = value - startVal;
      let step = 0;

      const interval = setInterval(() => {
        step++;
        const progress = step / steps;
        const eased = 1 - Math.pow(1 - progress, 3); // ease out cubic
        setDisplayValue(Math.round(startVal + diff * eased));
        if (step >= steps) {
          clearInterval(interval);
          setDisplayValue(value);
        }
      }, stepDuration);

      return () => clearInterval(interval);
    }
  }, [value]);

  const formatted = formatter ? formatter(displayValue) : displayValue.toString();

  return (
    <Animated.Text style={[style, { transform: [{ scale: scaleAnim }] }]}>
      {formatted}
    </Animated.Text>
  );
}
