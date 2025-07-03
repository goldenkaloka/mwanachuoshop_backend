export interface ApiContextType {
  fetchUserOffer: () => Promise<UserOfferType | null>;
}

const fetchUserOffer = useCallback(async (): Promise<UserOfferType | null> => {
  try {
    const data = await apiRequest('/shops/offers/me/', 'GET', undefined, 'application/json', true);
    return data;
  } catch (err) {
    return null;
  }
}, [apiRequest]);

const value: ApiContextType = {
  fetchUserOffer,
}; 