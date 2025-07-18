// src/screens/dashboard/DashboardScreen.tsx
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Dimensions,
  StatusBar,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useAppDispatch, useAppSelector } from '../../store/store';
import { 
  loadWorkOrders, 
  syncWorkOrders,
  selectWorkOrders,
  selectWorkOrdersLoading,
  selectWorkOrderStats 
} from '../../store/slices/workOrderSlice';
import { selectUser } from '../../store/slices/authSlice';
import { selectIsOnline, selectLastSyncTime } from '../../store/slices/syncSlice';
import { Card, Button, Badge, Loader } from '../../components/common';
import { theme } from '../../styles/theme';

const { width } = Dimensions.get('window');

interface QuickStatProps {
  title: string;
  value: number;
  icon: string;
  color: string;
  onPress?: () => void;
}

const QuickStat: React.FC<QuickStatProps> = ({ title, value, icon, color, onPress }) => (
  <TouchableOpacity 
    style={[styles.statCard, { borderLeftColor: color }]} 
    onPress={onPress}
    activeOpacity={0.8}
  >
    <View style={styles.statContent}>
      <View style={styles.statHeader}>
        <View style={[styles.statIcon, { backgroundColor: color + '15' }]}>
          <Icon name={icon} size={20} color={color} />
        </View>
        <Text style={styles.statValue}>{value}</Text>
      </View>
      <Text style={styles.statTitle}>{title}</Text>
    </View>
  </TouchableOpacity>
);

interface RecentActivityProps {
  activities: Array<{
    id: string;
    type: 'ot_created' | 'ot_completed' | 'sync' | 'scan';
    title: string;
    subtitle: string;
    time: string;
    icon: string;
    color: string;
  }>;
}

const RecentActivity: React.FC<RecentActivityProps> = ({ activities }) => (
  <Card style={styles.activityCard}>
    <View style={styles.cardHeader}>
      <Icon name="activity" size={20} color={theme.colors.primary[500]} />
      <Text style={styles.cardTitle}>Activité récente</Text>
    </View>
    
    {activities.length === 0 ? (
      <View style={styles.emptyState}>
        <Icon name="clock" size={32} color={theme.colors.gray[300]} />
        <Text style={styles.emptyText}>Aucune activité récente</Text>
      </View>
    ) : (
      <View style={styles.activityList}>
        {activities.map((activity, index) => (
          <View key={activity.id} style={styles.activityItem}>
            <View style={[styles.activityIcon, { backgroundColor: activity.color + '15' }]}>
              <Icon name={activity.icon} size={16} color={activity.color} />
            </View>
            <View style={styles.activityContent}>
              <Text style={styles.activityTitle}>{activity.title}</Text>
              <Text style={styles.activitySubtitle}>{activity.subtitle}</Text>
            </View>
            <Text style={styles.activityTime}>{activity.time}</Text>
          </View>
        ))}
      </View>
    )}
  </Card>
);

const DashboardScreen: React.FC = () => {
  const dispatch = useAppDispatch();
  const user = useAppSelector(selectUser);
  const workOrders = useAppSelector(selectWorkOrders);
  const loading = useAppSelector(selectWorkOrdersLoading);
  const stats = useAppSelector(selectWorkOrderStats);
  const isOnline = useAppSelector(selectIsOnline);
  const lastSyncTime = useAppSelector(selectLastSyncTime);

  const [refreshing, setRefreshing] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    // Charger les données initiales
    if (user?.id) {
      dispatch(loadWorkOrders(user.id));
    }

    // Mettre à jour l'heure toutes les minutes
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);

    return () => clearInterval(interval);
  }, [dispatch, user?.id]);

  const handleRefresh = async () => {
    if (!user?.id) return;
    
    setRefreshing(true);
    try {
      if (isOnline) {
        // Synchroniser avec le serveur si en ligne
        await dispatch(syncWorkOrders(user.id)).unwrap();
      } else {
        // Recharger depuis la base locale si hors ligne
        await dispatch(loadWorkOrders(user.id)).unwrap();
      }
    } catch (error) {
      console.error('Erreur refresh:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const getGreeting = () => {
    const hour = currentTime.getHours();
    if (hour < 12) return 'Bonjour';
    if (hour < 18) return 'Bon après-midi';
    return 'Bonsoir';
  };

  const formatLastSync = () => {
    if (!lastSyncTime) return 'Jamais';
    const date = new Date(lastSyncTime);
    const now = new Date();
    const diffMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffMinutes < 1) return 'À l\'instant';
    if (diffMinutes < 60) return `Il y a ${diffMinutes}min`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `Il y a ${diffHours}h`;
    return date.toLocaleDateString();
  };

  // Activités récentes simulées (à remplacer par de vraies données)
  const recentActivities = [
    {
      id: '1',
      type: 'ot_completed' as const,
      title: 'OT-2024-001 terminé',
      subtitle: 'Maintenance pompe centrifuge',
      time: '14h30',
      icon: 'check-circle',
      color: theme.colors.success[500],
    },
    {
      id: '2',
      type: 'scan' as const,
      title: 'Asset scanné',
      subtitle: 'Équipement EQ-789',
      time: '13h15',
      icon: 'camera',
      color: theme.colors.primary[500],
    },
    {
      id: '3',
      type: 'sync' as const,
      title: 'Synchronisation',
      subtitle: '5 éléments synchronisés',
      time: '12h00',
      icon: 'refresh-cw',
      color: theme.colors.secondary[500],
    },
  ];

  if (loading && workOrders.length === 0) {
    return (
      <View style={styles.container}>
        <Loader text="Chargement du tableau de bord..." />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={theme.colors.primary[500]} />
      
      {/* Header avec gradient */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <View style={styles.userInfo}>
            <Text style={styles.greeting}>{getGreeting()}</Text>
            <Text style={styles.userName}>{user?.first_name || user?.username}</Text>
          </View>
          
          <View style={styles.headerActions}>
            <TouchableOpacity style={styles.headerButton}>
              <Icon name="bell" size={20} color={theme.colors.white} />
              <View style={styles.notificationBadge}>
                <Text style={styles.notificationText}>3</Text>
              </View>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.headerButton}>
              <Icon name="settings" size={20} color={theme.colors.white} />
            </TouchableOpacity>
          </View>
        </View>
        
        {/* Statut de connexion */}
        <View style={styles.connectionStatus}>
          <View style={styles.statusIndicator}>
            <View style={[styles.statusDot, { 
              backgroundColor: isOnline ? theme.colors.success[500] : theme.colors.gray[400] 
            }]} />
            <Text style={styles.statusText}>
              {isOnline ? 'En ligne' : 'Hors ligne'}
            </Text>
          </View>
          <Text style={styles.lastSyncText}>
            Dernière sync: {formatLastSync()}
          </Text>
        </View>
      </View>

      <ScrollView
        style={styles.scrollContainer}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Statistiques rapides */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Vue d'ensemble</Text>
          <View style={styles.statsGrid}>
            <QuickStat
              title="Total assigné"
              value={stats.total}
              icon="clipboard"
              color={theme.colors.primary[500]}
            />
            <QuickStat
              title="En cours"
              value={stats.en_cours}
              icon="play-circle"
              color={theme.colors.secondary[500]}
            />
            <QuickStat
              title="Terminées"
              value={stats.termine}
              icon="check-circle"
              color={theme.colors.success[500]}
            />
            <QuickStat
              title="Urgentes"
              value={stats.urgent}
              icon="alert-triangle"
              color={theme.colors.error[500]}
            />
          </View>
        </View>

        {/* Actions rapides */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Actions rapides</Text>
          <View style={styles.quickActions}>
            <TouchableOpacity style={styles.actionCard}>
              <View style={[styles.actionIcon, { backgroundColor: theme.colors.primary[50] }]}>
                <Icon name="camera" size={24} color={theme.colors.primary[500]} />
              </View>
              <Text style={styles.actionTitle}>Scanner QR</Text>
              <Text style={styles.actionSubtitle}>Identifier un équipement</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.actionCard}>
              <View style={[styles.actionIcon, { backgroundColor: theme.colors.success[50] }]}>
                <Icon name="plus-circle" size={24} color={theme.colors.success[500]} />
              </View>
              <Text style={styles.actionTitle}>Nouvelle tâche</Text>
              <Text style={styles.actionSubtitle}>Créer un rapport</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.actionCard}>
              <View style={[styles.actionIcon, { backgroundColor: theme.colors.secondary[50] }]}>
                <Icon name="refresh-cw" size={24} color={theme.colors.secondary[500]} />
              </View>
              <Text style={styles.actionTitle}>Synchroniser</Text>
              <Text style={styles.actionSubtitle}>Mettre à jour les données</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.actionCard}>
              <View style={[styles.actionIcon, { backgroundColor: theme.colors.warning[50] }]}>
                <Icon name="map-pin" size={24} color={theme.colors.warning[500]} />
              </View>
              <Text style={styles.actionTitle}>Ma position</Text>
              <Text style={styles.actionSubtitle}>Voir ma géolocalisation</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Tâches prioritaires */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Tâches prioritaires</Text>
            <TouchableOpacity>
              <Text style={styles.seeAllText}>Voir tout</Text>
            </TouchableOpacity>
          </View>
          
          {workOrders.slice(0, 3).map((workOrder) => (
            <Card key={workOrder.id} style={styles.workOrderCard}>
              <View style={styles.workOrderHeader}>
                <View style={styles.workOrderInfo}>
                  <Text style={styles.workOrderTitle}>{workOrder.titre}</Text>
                  <Text style={styles.workOrderSubtitle}>
                    {workOrder.asset_name || 'Asset non défini'}
                  </Text>
                </View>
                <Badge
                  variant={
                    workOrder.priorite === 'URGENTE' ? 'error' :
                    workOrder.priorite === 'HAUTE' ? 'warning' :
                    workOrder.priorite === 'NORMALE' ? 'primary' : 'default'
                  }
                  size="sm"
                >
                  {workOrder.priorite}
                </Badge>
              </View>
              
              <View style={styles.workOrderMeta}>
                <View style={styles.metaItem}>
                  <Icon name="clock" size={14} color={theme.colors.gray[400]} />
                  <Text style={styles.metaText}>
                    {workOrder.date_planifiee ? 
                      new Date(workOrder.date_planifiee).toLocaleDateString() : 
                      'Non planifié'
                    }
                  </Text>
                </View>
                <View style={styles.metaItem}>
                  <Icon name="map-pin" size={14} color={theme.colors.gray[400]} />
                  <Text style={styles.metaText}>
                    {workOrder.localisation || 'Localisation non définie'}
                  </Text>
                </View>
              </View>
              
              <View style={styles.workOrderActions}>
                <Button variant="outline" size="sm" style={styles.actionButton}>
                  Voir détails
                </Button>
                <Button variant="primary" size="sm" style={styles.actionButton}>
                  Commencer
                </Button>
              </View>
            </Card>
          ))}
          
          {workOrders.length === 0 && (
            <Card style={styles.emptyWorkOrders}>
              <View style={styles.emptyState}>
                <Icon name="inbox" size={48} color={theme.colors.gray[300]} />
                <Text style={styles.emptyTitle}>Aucune tâche assignée</Text>
                <Text style={styles.emptyText}>
                  Vous n'avez actuellement aucun ordre de travail assigné.
                </Text>
              </View>
            </Card>
          )}
        </View>

        {/* Activité récente */}
        <View style={styles.section}>
          <RecentActivity activities={recentActivities} />
        </View>

        {/* Weather widget ou info contextuelle */}
        <View style={styles.section}>
          <Card style={styles.infoCard}>
            <View style={styles.infoHeader}>
              <Icon name="info" size={20} color={theme.colors.primary[500]} />
              <Text style={styles.infoTitle}>Conseil du jour</Text>
            </View>
            <Text style={styles.infoText}>
              N'oubliez pas de synchroniser vos données avant de partir en intervention pour avoir les dernières mises à jour.
            </Text>
          </Card>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background.secondary,
  },
  header: {
    backgroundColor: theme.colors.primary[500],
    paddingTop: 50,
    paddingHorizontal: theme.spacing[4],
    paddingBottom: theme.spacing[4],
    borderBottomLeftRadius: theme.borderRadius['2xl'],
    borderBottomRightRadius: theme.borderRadius['2xl'],
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing[4],
  },
  userInfo: {
    flex: 1,
  },
  greeting: {
    fontSize: theme.typography.sizes.base,
    color: theme.colors.white,
    opacity: 0.9,
    fontFamily: theme.typography.fonts.regular,
  },
  userName: {
    fontSize: theme.typography.sizes['2xl'],
    color: theme.colors.white,
    fontFamily: theme.typography.fonts.bold,
  },
  headerActions: {
    flexDirection: 'row',
    gap: theme.spacing[3],
  },
  headerButton: {
    position: 'relative',
    padding: theme.spacing[2],
  },
  notificationBadge: {
    position: 'absolute',
    top: 4,
    right: 4,
    backgroundColor: theme.colors.error[500],
    borderRadius: 8,
    minWidth: 16,
    height: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  notificationText: {
    fontSize: 10,
    color: theme.colors.white,
    fontFamily: theme.typography.fonts.bold,
  },
  connectionStatus: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: theme.spacing[2],
  },
  statusText: {
    fontSize: theme.typography.sizes.sm,
    color: theme.colors.white,
    fontFamily: theme.typography.fonts.medium,
  },
  lastSyncText: {
    fontSize: theme.typography.sizes.sm,
    color: theme.colors.white,
    opacity: 0.8,
    fontFamily: theme.typography.fonts.regular,
  },
  scrollContainer: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: theme.spacing[4],
    paddingTop: theme.spacing[6],
    paddingBottom: theme.spacing[8],
  },
  section: {
    marginBottom: theme.spacing[6],
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing[4],
  },
  sectionTitle: {
    fontSize: theme.typography.sizes.lg,
    fontFamily: theme.typography.fonts.semiBold,
    color: theme.colors.text.primary,
    marginBottom: theme.spacing[4],
  },
  seeAllText: {
    fontSize: theme.typography.sizes.sm,
    color: theme.colors.primary[500],
    fontFamily: theme.typography.fonts.medium,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing[3],
  },
  statCard: {
    flex: 1,
    minWidth: (width - theme.spacing[4] * 2 - theme.spacing[3]) / 2,
    backgroundColor: theme.colors.white,
    borderRadius: theme.borderRadius.lg,
    padding: theme.spacing[4],
    borderLeftWidth: 4,
    ...theme.shadows.sm,
  },
  statContent: {
    gap: theme.spacing[2],
  },
  statHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  statValue: {
    fontSize: theme.typography.sizes['2xl'],
    fontFamily: theme.typography.fonts.bold,
    color: theme.colors.text.primary,
  },
  statTitle: {
    fontSize: theme.typography.sizes.sm,
    fontFamily: theme.typography.fonts.medium,
    color: theme.colors.text.secondary,
  },
  quickActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing[3],
  },
  actionCard: {
    flex: 1,
    minWidth: (width - theme.spacing[4] * 2 - theme.spacing[3]) / 2,
    backgroundColor: theme.colors.white,
    borderRadius: theme.borderRadius.lg,
    padding: theme.spacing[4],
    alignItems: 'center',
    ...theme.shadows.sm,
  },
  actionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: theme.spacing[3],
  },
  actionTitle: {
    fontSize: theme.typography.sizes.base,
    fontFamily: theme.typography.fonts.semiBold,
    color: theme.colors.text.primary,
    textAlign: 'center',
    marginBottom: theme.spacing[1],
  },
  actionSubtitle: {
    fontSize: theme.typography.sizes.sm,
    fontFamily: theme.typography.fonts.regular,
    color: theme.colors.text.secondary,
    textAlign: 'center',
  },
  workOrderCard: {
    padding: theme.spacing[4],
    marginBottom: theme.spacing[3],
    backgroundColor: theme.colors.white,
  },
  workOrderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: theme.spacing[3],
  },
  workOrderInfo: {
    flex: 1,
    marginRight: theme.spacing[3],
  },
  workOrderTitle: {
    fontSize: theme.typography.sizes.base,
    fontFamily: theme.typography.fonts.semiBold,
    color: theme.colors.text.primary,
    marginBottom: theme.spacing[1],
  },
  workOrderSubtitle: {
    fontSize: theme.typography.sizes.sm,
    fontFamily: theme.typography.fonts.regular,
    color: theme.colors.text.secondary,
  },
  workOrderMeta: {
    gap: theme.spacing[2],
    marginBottom: theme.spacing[4],
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  metaText: {
    fontSize: theme.typography.sizes.sm,
    fontFamily: theme.typography.fonts.regular,
    color: theme.colors.text.tertiary,
    marginLeft: theme.spacing[2],
  },
  workOrderActions: {
    flexDirection: 'row',
    gap: theme.spacing[2],
  },
  actionButton: {
    flex: 1,
  },
  emptyWorkOrders: {
    padding: theme.spacing[6],
    alignItems: 'center',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: theme.spacing[4],
  },
  emptyTitle: {
    fontSize: theme.typography.sizes.lg,
    fontFamily: theme.typography.fonts.semiBold,
    color: theme.colors.text.primary,
    marginTop: theme.spacing[3],
    marginBottom: theme.spacing[2],
    textAlign: 'center',
  },
  emptyText: {
    fontSize: theme.typography.sizes.base,
    fontFamily: theme.typography.fonts.regular,
    color: theme.colors.text.secondary,
    textAlign: 'center',
    lineHeight: 22,
  },
  activityCard: {
    padding: theme.spacing[4],
    backgroundColor: theme.colors.white,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing[4],
  },
  cardTitle: {
    fontSize: theme.typography.sizes.lg,
    fontFamily: theme.typography.fonts.semiBold,
    color: theme.colors.text.primary,
    marginLeft: theme.spacing[2],
  },
  activityList: {
    gap: theme.spacing[3],
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: theme.spacing[2],
  },
  activityIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: theme.spacing[3],
  },
  activityContent: {
    flex: 1,
  },
  activityTitle: {
    fontSize: theme.typography.sizes.base,
    fontFamily: theme.typography.fonts.medium,
    color: theme.colors.text.primary,
    marginBottom: 2,
  },
  activitySubtitle: {
    fontSize: theme.typography.sizes.sm,
    fontFamily: theme.typography.fonts.regular,
    color: theme.colors.text.secondary,
  },
  activityTime: {
    fontSize: theme.typography.sizes.sm,
    fontFamily: theme.typography.fonts.regular,
    color: theme.colors.text.tertiary,
  },
  infoCard: {
    padding: theme.spacing[4],
    backgroundColor: theme.colors.primary[50],
    borderWidth: 1,
    borderColor: theme.colors.primary[100],
  },
  infoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing[2],
  },
  infoTitle: {
    fontSize: theme.typography.sizes.base,
    fontFamily: theme.typography.fonts.semiBold,
    color: theme.colors.primary[700],
    marginLeft: theme.spacing[2],
  },
  infoText: {
    fontSize: theme.typography.sizes.sm,
    fontFamily: theme.typography.fonts.regular,
    color: theme.colors.primary[600],
    lineHeight: 20,
  },
});

export default DashboardScreen;