import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as ImagePicker from 'expo-image-picker';

const COLORS = [
  { id: 'green', name: 'Verde', color: '#4CAF50' },
  { id: 'blue', name: 'Azul', color: '#2196F3' },
  { id: 'purple', name: 'Roxo', color: '#9C27B0' },
  { id: 'orange', name: 'Laranja', color: '#FF9800' },
  { id: 'red', name: 'Vermelho', color: '#F44336' },
  { id: 'yellow', name: 'Amarelo', color: '#FFC107' },
];

const ICONS: any[] = [
  { id: 'person', name: 'person' },
  { id: 'briefcase', name: 'briefcase' },
  { id: 'rocket', name: 'rocket' },
  { id: 'flash', name: 'flash' },
  { id: 'trophy', name: 'trophy' },
  { id: 'star', name: 'star' },
];

export default function AvatarSelection() {
  const router = useRouter();
  const [selectedColor, setSelectedColor] = useState('green');
  const [selectedIcon, setSelectedIcon] = useState('person');
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [photoBase64, setPhotoBase64] = useState<string | null>(null);

  const handleNext = async () => {
    await AsyncStorage.setItem('avatar_color', selectedColor);
    await AsyncStorage.setItem('avatar_icon', selectedIcon);
    if (photoBase64) {
      await AsyncStorage.setItem('avatar_photo', photoBase64);
    }
    router.push('/(onboarding)/background');
  };

  const pickImage = async () => {
    // Request permission
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (status !== 'granted') {
      Alert.alert('Permissão Necessária', 'Precisamos de permissão para acessar sua galeria');
      return;
    }

    // Pick image
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.5, // Compress to reduce size
      base64: true,
    });

    if (!result.canceled && result.assets[0].base64) {
      setPhotoUri(result.assets[0].uri);
      setPhotoBase64(`data:image/jpeg;base64,${result.assets[0].base64}`);
    }
  };

  const selectedColorData = COLORS.find(c => c.id === selectedColor);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        {/* Progress */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressDot, styles.progressDotActive]} />
          <View style={styles.progressDot} />
          <View style={styles.progressDot} />
          <View style={styles.progressDot} />
        </View>

        {/* Header */}
        <Text style={styles.title}>Escolha seu Avatar</Text>
        <Text style={styles.subtitle}>Selecione uma cor e um ícone para representar você</Text>

        {/* Preview */}
        <View style={styles.previewContainer}>
          {photoUri ? (
            <Image source={{ uri: photoUri }} style={styles.photoPreview} />
          ) : (
            <View
              style={[
                styles.avatarPreview,
                { backgroundColor: selectedColorData?.color || '#4CAF50' },
              ]}
            >
              <Ionicons name={selectedIcon as any} size={80} color="#fff" />
            </View>
          )}
        </View>

        {/* Photo Upload Button */}
        <TouchableOpacity style={styles.photoButton} onPress={pickImage}>
          <Ionicons name="camera" size={20} color="#fff" />
          <Text style={styles.photoButtonText}>
            {photoUri ? 'Trocar Foto' : 'Usar Minha Foto'}
          </Text>
        </TouchableOpacity>

        {photoUri && (
          <TouchableOpacity
            style={styles.removePhotoButton}
            onPress={() => {
              setPhotoUri(null);
              setPhotoBase64(null);
            }}
          >
            <Text style={styles.removePhotoText}>Usar Avatar ao Invés</Text>
          </TouchableOpacity>
        )}

        {!photoUri && (
          <>
            {/* Color Selection */}
            <Text style={styles.sectionTitle}>Cor</Text>
            <View style={styles.colorGrid}>
              {COLORS.map(color => (
                <TouchableOpacity
                  key={color.id}
                  style={[
                    styles.colorOption,
                    { backgroundColor: color.color },
                    selectedColor === color.id && styles.colorOptionSelected,
                  ]}
                  onPress={() => setSelectedColor(color.id)}
                >
                  {selectedColor === color.id && (
                    <Ionicons name="checkmark" size={24} color="#fff" />
                  )}
                </TouchableOpacity>
              ))}
            </View>

            {/* Icon Selection */}
            <Text style={styles.sectionTitle}>Ícone</Text>
            <View style={styles.iconGrid}>
              {ICONS.map(icon => (
                <TouchableOpacity
                  key={icon.id}
                  style={[
                    styles.iconOption,
                    selectedIcon === icon.id && styles.iconOptionSelected,
                  ]}
                  onPress={() => setSelectedIcon(icon.id)}
                >
                  <Ionicons name={icon.name} size={32} color={selectedIcon === icon.id ? '#4CAF50' : '#fff'} />
                </TouchableOpacity>
              ))}
            </View>
          </>
        )}

        {/* Next Button */}
        <TouchableOpacity style={styles.nextButton} onPress={handleNext}>
          <Text style={styles.nextButtonText}>Próximo</Text>
          <Ionicons name="arrow-forward" size={20} color="#fff" />
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  content: {
    padding: 24,
  },
  progressContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 32,
  },
  progressDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#3a3a3a',
  },
  progressDotActive: {
    backgroundColor: '#4CAF50',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#888',
    textAlign: 'center',
    marginBottom: 32,
  },
  previewContainer: {
    alignItems: 'center',
    marginBottom: 48,
  },
  avatarPreview: {
    width: 160,
    height: 160,
    borderRadius: 80,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  photoPreview: {
    width: 160,
    height: 160,
    borderRadius: 80,
  },
  photoButton: {
    backgroundColor: '#2196F3',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  photoButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  removePhotoButton: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    marginBottom: 24,
  },
  removePhotoText: {
    color: '#888',
    fontSize: 14,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
  },
  colorGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
    marginBottom: 32,
  },
  colorOption: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
  },
  colorOptionSelected: {
    borderWidth: 4,
    borderColor: '#fff',
  },
  iconGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
    marginBottom: 32,
  },
  iconOption: {
    width: 70,
    height: 70,
    borderRadius: 12,
    backgroundColor: '#2a2a2a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconOptionSelected: {
    backgroundColor: '#3a3a3a',
    borderWidth: 2,
    borderColor: '#4CAF50',
  },
  nextButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    height: 56,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    marginTop: 16,
  },
  nextButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});
