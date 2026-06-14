export function familyAppUrl(slug: string): string {
  return import.meta.env.BASE_URL + slug + '/';
}
