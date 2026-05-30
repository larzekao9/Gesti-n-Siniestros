import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const PUBLIC_PATHS = ['/login', '/register', '/mfa/setup', '/mfa/verify', '/forgot-password', '/reset-password']
const AUTH_REDIRECT = '/login'
const POST_AUTH_REDIRECT = '/dashboard'

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl

  // Normalize root
  if (pathname === '/') {
    const token = request.cookies.get('siniestros_access_token')?.value
    if (token) {
      return NextResponse.redirect(new URL(POST_AUTH_REDIRECT, request.url))
    }
    return NextResponse.redirect(new URL(AUTH_REDIRECT, request.url))
  }

  const isPublic = PUBLIC_PATHS.some(
    (path) => pathname === path || pathname.startsWith(`${path}/`)
  )

  if (isPublic) {
    return NextResponse.next()
  }

  // Protect dashboard routes — check cookie (server-side accessible)
  // The access token cookie is written by the client after successful login.
  // Falls back gracefully: missing cookie → redirect to login.
  const token = request.cookies.get('siniestros_access_token')?.value
  if (!token) {
    const loginUrl = new URL(AUTH_REDIRECT, request.url)
    loginUrl.searchParams.set('from', pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except static files and Next.js internals.
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|css|js)$).*)',
  ],
}
