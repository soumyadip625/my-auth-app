import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";

const handler = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID ?? "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
    }),
  ],
  pages: {
    signIn: '/login',
  },
  callbacks: {
    async redirect() {
      return '/dashboard';
    },
    async session({ session }) {
      return session;
    },
  },
  debug: true,
});

export { handler as GET, handler as POST }; 