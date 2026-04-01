import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

export default function Investments() {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Investimentos</Text>
        <Ionicons name="trending-up" size={32} color="#4CAF50" />
      </View>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.comingSoon}>
          <Ionicons name="construct" size={64} color="#888" />
          <Text style={styles.comingSoonText}>Em breve!</Text>
          <Text style={styles.comingSoonDesc}>
            Investimentos reais em ações, cripto, commodities e forex
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a2a',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  comingSoon: {
    alignItems: 'center',
  },
  comingSoonText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 16,
  },
  comingSoonDesc: {
    fontSize: 16,
    color: '#888',
    textAlign: 'center',
    marginTop: 8,
  },
});
