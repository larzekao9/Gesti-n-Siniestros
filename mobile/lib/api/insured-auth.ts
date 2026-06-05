import { api } from './client'
import { API_BASE_URL } from '../config'
import axios from 'axios'
import type { Account, InsuredTokenResponse } from '@/types/auth'

// Login y registro NO llevan token previo y necesitan el header X-Tenant-Slug
// solo en login (el tenant va en el body). Usamos axios directo para no depender
// del interceptor de sesión.

export async function login(args: {
  email: string
  password: string
  tenant_slug: string
}): Promise<InsuredTokenResponse> {
  const { data } = await axios.post(`${API_BASE_URL}/insured-auth/login`, args)
  return data
}

export async function registerWithToken(args: {
  activation_token: string
  password: string
}): Promise<InsuredTokenResponse> {
  const { data } = await axios.post(`${API_BASE_URL}/insured-auth/register`, args)
  return data
}

export async function forgotPassword(args: {
  email: string
  tenant_slug: string
}): Promise<void> {
  await axios.post(`${API_BASE_URL}/insured-auth/forgot-password`, args)
}

export async function logout(refresh_token: string): Promise<void> {
  await axios.post(`${API_BASE_URL}/insured-auth/logout`, { refresh_token })
}

export async function getMe(): Promise<Account> {
  const { data } = await api.get('/insured-auth/me')
  return data
}

export async function registerDeviceToken(args: {
  expo_push_token: string
  platform: 'ios' | 'android'
}): Promise<void> {
  await api.post('/insured-auth/register-device-token', args)
}

export async function unregisterDeviceToken(expo_push_token: string): Promise<void> {
  await api.post('/insured-auth/unregister-device-token', {
    expo_push_token,
    platform: 'android',
  })
}
