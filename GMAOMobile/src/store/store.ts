// src/store/store.ts - Version simplifiée temporaire
import { configureStore, combineReducers } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Import seulement les slices qui existent
import authSlice from './slices/authSlice';
import syncSlice from './slices/syncSlice';
import networkSlice from './slices/networkSlice';
import settingsSlice from './slices/settingsSlice';

// Configuration de persistance
const persistConfig = {
  key: 'root',
  storage: AsyncStorage,
  whitelist: ['auth', 'settings'],
};

// Combinaison des reducers (seulement ceux qui existent)
const rootReducer = combineReducers({
  auth: authSlice,
  sync: syncSlice,
  network: networkSlice,
  settings: settingsSlice,
});

// Reducer principal avec persistance
const persistedReducer = persistReducer(persistConfig, rootReducer);

// Configuration du store
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [
          'persist/PERSIST',
          'persist/REHYDRATE',
          'persist/PAUSE',
          'persist/PURGE',
          'persist/REGISTER',
          'persist/FLUSH',
        ],
      },
    }),
});

export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;