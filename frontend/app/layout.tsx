import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import './globals.css';
import { AccessibilityProvider, STORAGE_KEY } from '@/lib/accessibility';

export const metadata: Metadata = {
  title: 'EyeAssist',
  description: 'Hệ thống tương tác đa phương thức hỗ trợ người suy giảm thị lực tiếp cận tài liệu số',
};

const themeScript = `try{var p=JSON.parse(localStorage.getItem('${STORAGE_KEY}')||'null');var t=p&&p.contrast;if(t==='standard'||t==='dark-yellow'||t==='light-black'){document.documentElement.dataset.theme=t}else if(window.matchMedia('(prefers-contrast: more)').matches){document.documentElement.dataset.theme='light-black'}}catch(e){}`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi" data-theme="standard" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <AccessibilityProvider>{children}</AccessibilityProvider>
      </body>
    </html>
  );
}
