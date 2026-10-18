import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const botUrl = process.env.NEXT_PUBLIC_BOT_URL || 'http://localhost:8080';
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
      elapsed: 0,
      is_playing: false
    }, { status: 500 });
  }
}