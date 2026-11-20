import { redirect } from 'next/navigation';

export default function MocksIndex() {
  redirect('/mocks/home');
}
