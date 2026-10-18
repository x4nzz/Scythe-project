import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const botUrl = process.env.NEXT_PUBLIC_BOT_URL || 'http://localhost:8080';
    const response = await fetch(`${botUrl}/api/stats`);

    if (!response.ok) {
      throw new Error('Failed to fetch stats from bot');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching stats:', error);
    // Return default values on error
    return NextResponse.json({
      servers: 0,
      users: 0,
      commands_used: 0,
      uptime: 0
    }, { status: 500 });
  }
}