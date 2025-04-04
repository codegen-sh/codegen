import OpenAI from 'openai';
import { NextResponse } from 'next/server';

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: Request) {
  try {
    const { logData } = await request.json();

    const chatCompletion = await client.chat.completions.create({
      messages: [
        {
          role: 'system',
          content: 'Make this a one line description of what is happening or guess what is happening with this software agent. Be confident and concise, phrasing it like "Running a process to do X" or "Investigating X to do Y". No parenthesis in output.'
        },
        { role: 'user', content: logData }
      ],
      model: 'gpt-4o-mini',
    });

    return NextResponse.json({
      content: chatCompletion.choices[0].message.content
    });
  } catch (error) {
    console.error('Error in clean-log API route:', error);
    return NextResponse.json(
      { error: 'Failed to process log' },
      { status: 500 }
    );
  }
}