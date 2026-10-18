import { NextResponse } from 'next/server';

export async function GET() {
  // If we are in a build phase, return mock data to prevent fetch errors during prerendering
  if (process.env.NEXT_PHASE === 'phase-production-build') {
    return NextResponse.json({
      title: '',
      artist: '',
      uri: '',
      artwork: '',
      duration: 0,
      started_at: 0,
      is_playing: false
    });
  }

  try {
    const botUrl = process.env.NEXT_PUBLIC_BOT_API_URL || process.env.NEXT_PUBLIC_BOT_URL || 'http://localhost:8080';
    const response = await fetch(`${botUrl}/api/now-playing`);

    if (!response.ok) {
      throw new Error('Failed to fetch now playing from bot');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching now playing:', error);
    // Return default values on error
    return NextResponse.json({
      title: '',
      artist: '',
      uri: '',
      artwork: '',
      duration: 0,
      started_at: 0,
      is_playing: false
    }, { status: 500 });
  }
}