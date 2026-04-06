import React, { useEffect, useState, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
  Modal,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { WebView } from 'react-native-webview';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
  const { colors } = useTheme();
import { useTheme } from '../../context/ThemeContext';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Company {
  id: string;
  name: string;
  category: string;
  lat: number;
  lng: number;
  description: string;
  employees: number;
  revenue: string;
  rating: number;
  city: string;
  icon: string;
  color: string;
  open_positions: number;
  investment_available: boolean;
  min_investment: number;
}

interface CategoryInfo {
  [key: string]: { icon: string; color: string };
}

const CATEGORY_LABELS: Record<string, string> = {
  tecnologia: 'Tecnologia',
  financeiro: 'Financeiro',
  alimentacao: 'Alimentação',
  construcao: 'Construção',
  varejo: 'Varejo',
  energia: 'Energia',
  saude: 'Saúde',
  marketing: 'Marketing',
  turismo: 'Turismo',
  mineracao: 'Mineração',
  logistica: 'Logística',
  agronegocio: 'Agronegócio',
};

function generateMapHTML(companies: Company[], categories: CategoryInfo): string {
  const markers = companies.map(c => {
    const catColor = c.color || '#888';
    return `{
      lat: ${c.lat},
      lng: ${c.lng},
      id: "${c.id}",
      name: "${c.name.replace(/"/g, '\\"')}",
      category: "${c.category}",
      color: "${catColor}",
      city: "${c.city}",
      employees: ${c.employees},
      rating: ${c.rating},
      description: "${c.description.replace(/"/g, '\\"')}",
      revenue: "${c.revenue}",
      positions: ${c.open_positions},
      investment: ${c.investment_available},
      minInvest: ${c.min_investment}
    }`;
  });

  return `
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #1a1a1a; overflow: hidden; }
    #map { width: 100vw; height: 100vh; }
    .custom-marker {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      border: 3px solid #fff;
      font-size: 16px;
      color: #fff;
      box-shadow: 0 2px 8px rgba(0,0,0,0.5);
      cursor: pointer;
      transition: transform 0.2s;
    }
    .custom-marker:hover { transform: scale(1.2); }
    .leaflet-popup-content-wrapper {
      background: #2a2a2a;
      border-radius: 12px;
      border: 1px solid #3a3a3a;
    }
    .leaflet-popup-content {
      color: #fff;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      margin: 12px;
    }
    .leaflet-popup-tip { background: #2a2a2a; }
    .popup-name { font-size: 16px; font-weight: bold; margin-bottom: 4px; }
    .popup-desc { font-size: 12px; color: #aaa; margin-bottom: 8px; }
    .popup-info { font-size: 11px; color: #888; }
    .popup-btn {
      display: inline-block;
      background: #4CAF50;
      color: #fff;
      border: none;
      padding: 6px 12px;
      border-radius: 6px;
      margin-top: 8px;
      cursor: pointer;
      font-size: 12px;
      font-weight: bold;
    }
    .popup-rating { color: #FFD700; font-weight: bold; }
    .popup-positions { color: #4CAF50; }
    .leaflet-control-zoom a { background: #2a2a2a !important; color: #fff !important; border-color: #3a3a3a !important; }
    .leaflet-control-attribution { display: none; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    var map = L.map('map', {
      zoomControl: true,
      attributionControl: false,
    }).setView([-23.5505, -46.6333], 12);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
    }).addTo(map);

    var companies = [${markers.join(',\n')}];

    var categoryIcons = {
      tecnologia: '💻', financeiro: '💰', alimentacao: '🍽️',
      construcao: '🏗️', varejo: '🛒', energia: '⚡',
      saude: '🏥', marketing: '📢', turismo: '✈️',
      mineracao: '⛏️', logistica: '🚛', agronegocio: '🌱'
    };

    var markers = [];

    companies.forEach(function(c) {
      var emoji = categoryIcons[c.category] || '🏢';
      var icon = L.divIcon({
        className: 'custom-div-icon',
        html: '<div class="custom-marker" style="background:' + c.color + '">' + emoji + '</div>',
        iconSize: [36, 36],
        iconAnchor: [18, 18],
        popupAnchor: [0, -20]
      });

      var posText = c.positions > 0 ? '<br><span class="popup-positions">' + c.positions + ' vagas abertas</span>' : '';
      var investText = c.investment ? '<br>Investimento mín: R$ ' + c.minInvest.toLocaleString('pt-BR') : '';

      var popup = '<div class="popup-name">' + c.name + '</div>' +
        '<div class="popup-desc">' + c.description + '</div>' +
        '<div class="popup-info">' +
        '📍 ' + c.city + '<br>' +
        '👥 ' + c.employees + ' funcionários<br>' +
        '💵 ' + c.revenue + '<br>' +
        '<span class="popup-rating">⭐ ' + c.rating.toFixed(1) + '</span>' +
        posText + investText +
        '</div>' +
        '<button class="popup-btn" onclick="selectCompany(\\'' + c.id + '\\')">Ver Detalhes</button>';

      var m = L.marker([c.lat, c.lng], {icon: icon}).addTo(map).bindPopup(popup);
      m.companyData = c;
      markers.push(m);
    });

    function selectCompany(id) {
      window.ReactNativeWebView.postMessage(JSON.stringify({type: 'select', companyId: id}));
    }

    function filterByCategory(cat) {
      markers.forEach(function(m) {
        if (cat === 'all' || m.companyData.category === cat) {
          m.addTo(map);
        } else {
          map.removeLayer(m);
        }
      });
    }

    function flyToCity(lat, lng, zoom) {
      map.flyTo([lat, lng], zoom || 13, { duration: 1.5 });
    }

    // Listen for messages from React Native
    document.addEventListener('message', function(e) {
      try {
        var msg = JSON.parse(e.data);
        if (msg.type === 'filter') filterByCategory(msg.category);
        if (msg.type === 'flyTo') flyToCity(msg.lat, msg.lng, msg.zoom);
      } catch(err) {}
    });
    window.addEventListener('message', function(e) {
      try {
        var msg = JSON.parse(e.data);
        if (msg.type === 'filter') filterByCategory(msg.category);
        if (msg.type === 'flyTo') flyToCity(msg.lat, msg.lng, msg.zoom);
      } catch(err) {}
    });
  </script>
</body>
</html>`;
}

export default function MapScreen() {
  const { token } = useAuth();
  const webViewRef = useRef<WebView>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [categories, setCategories] = useState<CategoryInfo>({});
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [showDetail, setShowDetail] = useState(false);

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      const res = await axios.get(
        `${EXPO_PUBLIC_BACKEND_URL}/api/map/companies`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCompanies(res.data.companies);
      setCategories(res.data.categories);
    } catch (error) {
      console.error('Error loading map companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterCategory = (cat: string) => {
    setSelectedCategory(cat);
    webViewRef.current?.postMessage(JSON.stringify({ type: 'filter', category: cat }));
  };

  const handleFlyToCity = (lat: number, lng: number) => {
    webViewRef.current?.postMessage(JSON.stringify({ type: 'flyTo', lat, lng, zoom: 13 }));
  };

  const handleWebViewMessage = (event: any) => {
    try {
      const msg = JSON.parse(event.nativeEvent.data);
      if (msg.type === 'select') {
        const company = companies.find(c => c.id === msg.companyId);
        if (company) {
          setSelectedCompany(company);
          setShowDetail(true);
        }
      }
    } catch (error) {
      console.error('Error parsing webview message:', error);
    }
  };

  const cities = [
    { name: 'São Paulo', lat: -23.5505, lng: -46.6333 },
    { name: 'Rio de Janeiro', lat: -22.9068, lng: -43.1729 },
    { name: 'Belo Horizonte', lat: -19.9167, lng: -43.9345 },
    { name: 'Curitiba', lat: -25.4284, lng: -49.2733 },
    { name: 'Porto Alegre', lat: -30.0346, lng: -51.2177 },
  ];

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4CAF50" />
          <Text style={styles.loadingText}>Carregando mapa...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const mapHTML = generateMapHTML(companies, categories);

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* City Quick Nav */}
      <View style={styles.topBar}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.cityRow}>
            {cities.map(city => (
              <TouchableOpacity
                key={city.name}
                style={styles.cityChip}
                onPress={() => handleFlyToCity(city.lat, city.lng)}
              >
                <Ionicons name="location" size={14} color="#4CAF50" />
                <Text style={styles.cityChipText}>{city.name}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </View>

      {/* Category Filters */}
      <View style={styles.filterBar}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.filterRow}>
            <TouchableOpacity
              style={[styles.filterChip, selectedCategory === 'all' && styles.filterChipActive]}
              onPress={() => handleFilterCategory('all')}
            >
              <Text style={[styles.filterChipText, selectedCategory === 'all' && styles.filterChipTextActive]}>
                Todos ({companies.length})
              </Text>
            </TouchableOpacity>
            {Object.entries(categories).map(([key, info]) => {
              const count = companies.filter(c => c.category === key).length;
              if (count === 0) return null;
              return (
                <TouchableOpacity
                  key={key}
                  style={[
                    styles.filterChip,
                    selectedCategory === key && styles.filterChipActive,
                    selectedCategory === key && { backgroundColor: info.color },
                  ]}
                  onPress={() => handleFilterCategory(key)}
                >
                  <Text style={[
                    styles.filterChipText,
                    selectedCategory === key && styles.filterChipTextActive,
                  ]}>
                    {CATEGORY_LABELS[key] || key} ({count})
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </ScrollView>
      </View>

      {/* Map WebView */}
      <View style={styles.mapContainer}>
        {Platform.OS === 'web' ? (
          <iframe
            srcDoc={mapHTML}
            style={{ width: '100%', height: '100%', border: 'none' } as any}
            title="map"
          />
        ) : (
          <WebView
            ref={webViewRef}
            source={{ html: mapHTML }}
            style={styles.webview}
            onMessage={handleWebViewMessage}
            javaScriptEnabled={true}
            domStorageEnabled={true}
            startInLoadingState={true}
            renderLoading={() => (
              <View style={styles.webviewLoading}>
                <ActivityIndicator size="large" color="#4CAF50" />
              </View>
            )}
          />
        )}
      </View>

      {/* Company Detail Modal */}
      <Modal
        visible={showDetail}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowDetail(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.detailSheet}>
            {selectedCompany && (
              <>
                <View style={styles.sheetHandle} />

                <View style={styles.detailHeader}>
                  <View style={[styles.detailIcon, { backgroundColor: selectedCompany.color }]}>
                    <Text style={styles.detailIconText}>
                      {selectedCompany.category === 'tecnologia' ? '💻' :
                       selectedCompany.category === 'financeiro' ? '💰' :
                       selectedCompany.category === 'alimentacao' ? '🍽️' :
                       selectedCompany.category === 'energia' ? '⚡' :
                       selectedCompany.category === 'saude' ? '🏥' :
                       selectedCompany.category === 'varejo' ? '🛒' :
                       selectedCompany.category === 'marketing' ? '📢' :
                       selectedCompany.category === 'construcao' ? '🏗️' : '🏢'}
                    </Text>
                  </View>
                  <View style={styles.detailTitleArea}>
                    <Text style={styles.detailName}>{selectedCompany.name}</Text>
                    <Text style={styles.detailCategory}>
                      {CATEGORY_LABELS[selectedCompany.category]} - {selectedCompany.city}
                    </Text>
                  </View>
                  <TouchableOpacity onPress={() => setShowDetail(false)}>
                    <Ionicons name="close-circle" size={32} color="#888" />
                  </TouchableOpacity>
                </View>

                <Text style={styles.detailDesc}>{selectedCompany.description}</Text>

                <View style={styles.detailGrid}>
                  <View style={styles.detailGridItem}>
                    <Ionicons name="people" size={20} color="#2196F3" />
                    <Text style={styles.detailGridValue}>{selectedCompany.employees}</Text>
                    <Text style={styles.detailGridLabel}>Funcionários</Text>
                  </View>
                  <View style={styles.detailGridItem}>
                    <Ionicons name="star" size={20} color="#FFD700" />
                    <Text style={styles.detailGridValue}>{selectedCompany.rating.toFixed(1)}</Text>
                    <Text style={styles.detailGridLabel}>Avaliação</Text>
                  </View>
                  <View style={styles.detailGridItem}>
                    <Ionicons name="cash" size={20} color="#4CAF50" />
                    <Text style={styles.detailGridValue}>{selectedCompany.revenue}</Text>
                    <Text style={styles.detailGridLabel}>Receita</Text>
                  </View>
                </View>

                {selectedCompany.open_positions > 0 && (
                  <View style={styles.positionsCard}>
                    <Ionicons name="briefcase" size={20} color="#4CAF50" />
                    <Text style={styles.positionsText}>
                      {selectedCompany.open_positions} vagas abertas
                    </Text>
                  </View>
                )}

                {selectedCompany.investment_available && (
                  <View style={styles.investCard}>
                    <Ionicons name="trending-up" size={20} color="#FF9800" />
                    <View style={styles.investInfo}>
                      <Text style={styles.investText}>Investimento disponível</Text>
                      <Text style={styles.investMin}>
                        Mínimo: R$ {selectedCompany.min_investment.toLocaleString('pt-BR')}
                      </Text>
                    </View>
                  </View>
                )}
              </>
            )}
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a1a' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 12 },
  loadingText: { color: '#888', fontSize: 16 },

  // Top bar
  topBar: {
    backgroundColor: '#1a1a1a',
    paddingHorizontal: 8,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a2a',
  },
  cityRow: { flexDirection: 'row', gap: 8, paddingHorizontal: 4 },
  cityChip: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: '#2a2a2a', borderRadius: 16, paddingHorizontal: 12, paddingVertical: 6,
  },
  cityChipText: { color: '#ccc', fontSize: 12, fontWeight: 'bold' },

  // Filter bar
  filterBar: {
    backgroundColor: '#1a1a1a',
    paddingHorizontal: 8,
    paddingVertical: 6,
  },
  filterRow: { flexDirection: 'row', gap: 6, paddingHorizontal: 4 },
  filterChip: {
    backgroundColor: '#2a2a2a', borderRadius: 16,
    paddingHorizontal: 12, paddingVertical: 6,
  },
  filterChipActive: { backgroundColor: '#4CAF50' },
  filterChipText: { color: '#888', fontSize: 11, fontWeight: 'bold' },
  filterChipTextActive: { color: '#fff' },

  // Map
  mapContainer: { flex: 1 },
  webview: { flex: 1 },
  webviewLoading: {
    position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
    justifyContent: 'center', alignItems: 'center', backgroundColor: '#1a1a1a',
  },

  // Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  detailSheet: {
    backgroundColor: '#1a1a1a', borderTopLeftRadius: 24, borderTopRightRadius: 24,
    padding: 24, maxHeight: '65%',
  },
  sheetHandle: {
    width: 40, height: 4, backgroundColor: '#555', borderRadius: 2,
    alignSelf: 'center', marginBottom: 16,
  },
  detailHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 16, gap: 12 },
  detailIcon: {
    width: 48, height: 48, borderRadius: 12, justifyContent: 'center', alignItems: 'center',
  },
  detailIconText: { fontSize: 24 },
  detailTitleArea: { flex: 1 },
  detailName: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  detailCategory: { fontSize: 13, color: '#888', marginTop: 2 },
  detailDesc: { fontSize: 14, color: '#aaa', lineHeight: 20, marginBottom: 16 },

  detailGrid: { flexDirection: 'row', gap: 12, marginBottom: 16 },
  detailGridItem: {
    flex: 1, backgroundColor: '#2a2a2a', borderRadius: 12, padding: 12, alignItems: 'center',
  },
  detailGridValue: { color: '#fff', fontSize: 16, fontWeight: 'bold', marginTop: 6 },
  detailGridLabel: { color: '#666', fontSize: 11, marginTop: 2 },

  positionsCard: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: '#2a3a2a', borderRadius: 12, padding: 16, marginBottom: 12,
    borderWidth: 1, borderColor: '#4CAF50',
  },
  positionsText: { color: '#4CAF50', fontSize: 16, fontWeight: 'bold' },

  investCard: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: '#3a2a1a', borderRadius: 12, padding: 16,
    borderWidth: 1, borderColor: '#FF9800',
  },
  investInfo: { flex: 1 },
  investText: { color: '#FF9800', fontSize: 14, fontWeight: 'bold' },
  investMin: { color: '#888', fontSize: 12, marginTop: 2 },
});
