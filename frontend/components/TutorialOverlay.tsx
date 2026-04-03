import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Animated, Dimensions, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useLanguage } from '../context/LanguageContext';

const { width, height } = Dimensions.get('window');

interface TutorialStep {
  icon: string;
  titleKey: string;
  descKey: string;
  color: string;
}

const STEPS: TutorialStep[] = [
  { icon: 'home', titleKey: 'tutorial.welcomeTitle', descKey: 'tutorial.welcomeDesc', color: '#4CAF50' },
  { icon: 'briefcase', titleKey: 'tutorial.jobsTitle', descKey: 'tutorial.jobsDesc', color: '#2196F3' },
  { icon: 'business', titleKey: 'tutorial.companiesTitle', descKey: 'tutorial.companiesDesc', color: '#FF9800' },
  { icon: 'trending-up', titleKey: 'tutorial.investTitle', descKey: 'tutorial.investDesc', color: '#9C27B0' },
  { icon: 'card', titleKey: 'tutorial.bankTitle', descKey: 'tutorial.bankDesc', color: '#1E88E5' },
  { icon: 'trophy', titleKey: 'tutorial.rankTitle', descKey: 'tutorial.rankDesc', color: '#FFD700' },
];

const TUTORIAL_KEY = 'bizrealms_tutorial_done';

export default function TutorialOverlay() {
  const [visible, setVisible] = useState(false);
  const [step, setStep] = useState(0);
  const fadeAnim = useState(new Animated.Value(0))[0];
  const slideAnim = useState(new Animated.Value(50))[0];
  const { t } = useLanguage();

  useEffect(() => {
    checkTutorial();
  }, []);

  const checkTutorial = async () => {
    try {
      const done = await AsyncStorage.getItem(TUTORIAL_KEY);
      if (!done) {
        setVisible(true);
        animateIn();
      }
    } catch (e) {
      // ignore
    }
  };

  const animateIn = () => {
    slideAnim.setValue(50);
    fadeAnim.setValue(0);
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 400, useNativeDriver: true }),
      Animated.spring(slideAnim, { toValue: 0, useNativeDriver: true, speed: 14, bounciness: 6 }),
    ]).start();
  };

  const handleNext = () => {
    if (step < STEPS.length - 1) {
      setStep(s => s + 1);
      animateIn();
    } else {
      handleDismiss();
    }
  };

  const handleDismiss = async () => {
    Animated.timing(fadeAnim, { toValue: 0, duration: 300, useNativeDriver: true }).start(() => {
      setVisible(false);
    });
    try { await AsyncStorage.setItem(TUTORIAL_KEY, 'true'); } catch (e) {}
  };

  if (!visible) return null;

  const current = STEPS[step];

  return (
    <Animated.View style={[s.overlay, { opacity: fadeAnim }]}>
      <Animated.View style={[s.card, { transform: [{ translateY: slideAnim }] }]}>
        <View style={[s.iconCircle, { backgroundColor: current.color + '22' }]}> 
          <Ionicons name={current.icon as any} size={48} color={current.color} />
        </View>

        <Text style={s.title}>{t(current.titleKey)}</Text>
        <Text style={s.desc}>{t(current.descKey)}</Text>

        {/* Progress dots */}
        <View style={s.dots}>
          {STEPS.map((_, i) => (
            <View key={i} style={[s.dot, i === step && { backgroundColor: current.color, width: 24 }]} />
          ))}
        </View>

        <View style={s.buttons}>
          <TouchableOpacity onPress={handleDismiss} style={s.skipBtn}>
            <Text style={s.skipText}>{t('tutorial.skip')}</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={handleNext} style={[s.nextBtn, { backgroundColor: current.color }]}>
            <Text style={s.nextText}>{step < STEPS.length - 1 ? t('tutorial.next') : t('tutorial.start')}</Text>
            <Ionicons name={step < STEPS.length - 1 ? 'arrow-forward' : 'rocket'} size={18} color="#fff" />
          </TouchableOpacity>
        </View>
      </Animated.View>
    </Animated.View>
  );
}

const s = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.85)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 9999,
    padding: 24,
  },
  card: {
    backgroundColor: '#1e1e2e',
    borderRadius: 24,
    padding: 32,
    width: '100%',
    maxWidth: 380,
    alignItems: 'center',
  },
  iconCircle: {
    width: 96,
    height: 96,
    borderRadius: 48,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 12,
  },
  desc: {
    fontSize: 15,
    color: '#aaa',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 24,
  },
  dots: {
    flexDirection: 'row',
    gap: 6,
    marginBottom: 24,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#444',
  },
  buttons: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  skipBtn: {
    flex: 1,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#444',
  },
  skipText: {
    color: '#888',
    fontSize: 15,
  },
  nextBtn: {
    flex: 2,
    height: 48,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 12,
    gap: 8,
  },
  nextText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
