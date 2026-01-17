import "./globals.css";
import Navbar from "../components/Navbar";
import Providers from "../components/Providers";

export const metadata = {
  title: "Fuck The Exam - N1 Quiz App",
  description: "Master Japanese N1 with AI-powered quizzes",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <Navbar />
          <main className="container mx-auto px-4 py-8">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
