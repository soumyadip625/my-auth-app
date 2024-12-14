'use client';

import React from 'react';
import { signIn } from "next-auth/react";
import Image from "next/image";

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-xl shadow-lg">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-bold text-gray-900">Welcome back</h2>
          <p className="mt-2 text-sm text-gray-600">Please sign in to continue</p>
        </div>
        
        <button
          onClick={() => signIn('google', { callbackUrl: '/dashboard' })}
          className="w-full flex items-center justify-center gap-3 bg-white hover:bg-gray-50 text-gray-700 font-semibold py-3 px-4 border border-gray-300 rounded-lg shadow-sm transition-all"
        >
          <Image
            src="/google.svg"
            alt="Google logo"
            width={20}
            height={20}
          />
          Continue with Google
        </button>
      </div>
    </div>
  );
} 