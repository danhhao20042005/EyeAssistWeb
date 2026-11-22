// Cho phép Node chạy trực tiếp các file .ts của dự án: bỏ qua việc thiếu đuôi .ts và alias "@/".
import { register } from 'node:module';
register('./ts-resolver.mjs', import.meta.url);
