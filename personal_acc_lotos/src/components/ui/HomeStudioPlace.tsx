import { Icon24PlaceOutline } from '@vkontakte/icons'
import type { StudioPlace } from '../../types/studio'
import { openVkUrl } from '../../vkBridge'
import './HomeStudioPlace.css'

type HomeStudioPlaceProps = {
  place: StudioPlace | null
}

function buildMapWidgetUrl(place: StudioPlace): string | null {
  if (place.latitude != null && place.longitude != null) {
    const ll = `${place.longitude},${place.latitude}`
    const pt = `${place.longitude},${place.latitude},pm2rdm`
    return `https://yandex.ru/map-widget/v1/?ll=${encodeURIComponent(ll)}&z=16&pt=${encodeURIComponent(pt)}`
  }
  if (place.address) {
    return `https://yandex.ru/map-widget/v1/?mode=search&text=${encodeURIComponent(place.address)}`
  }
  return null
}

export function HomeStudioPlace({ place }: HomeStudioPlaceProps) {
  if (!place) {
    return null
  }

  const mapWidgetUrl = buildMapWidgetUrl(place)

  return (
    <section className="home-studio-place" aria-label="Как нас найти">
      <h3 className="lotos-section-title home-studio-place__title">Как нас найти</h3>
      <div className="home-studio-place__card lotos-card">
        {mapWidgetUrl && (
          <div className="home-studio-place__map-wrap">
            <iframe
              title="Карта студии"
              className="home-studio-place__map"
              src={mapWidgetUrl}
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
            />
          </div>
        )}

        <div className="home-studio-place__info">
          <div className="home-studio-place__heading">
            <Icon24PlaceOutline className="home-studio-place__icon" aria-hidden="true" />
            {place.address && (
              <p className="home-studio-place__address">{place.address}</p>
            )}
          </div>

          {place.hours && (
            <div className="home-studio-place__row">
              <span className="home-studio-place__label">Время работы</span>
              <span className="home-studio-place__value">{place.hours}</span>
            </div>
          )}

          {place.phone && (
            <div className="home-studio-place__row">
              <span className="home-studio-place__label">Телефон</span>
              <a className="home-studio-place__link" href={`tel:${place.phone.replace(/\s/g, '')}`}>
                {place.phone}
              </a>
            </div>
          )}

          <div className="home-studio-place__actions">
            {place.mapUrl && (
              <button
                type="button"
                className="lotos-btn lotos-btn--secondary home-studio-place__btn"
                onClick={() => void openVkUrl(place.mapUrl as string)}
              >
                Открыть на карте
              </button>
            )}
            {place.groupUrl && (
              <button
                type="button"
                className="lotos-btn lotos-btn--secondary home-studio-place__btn"
                onClick={() => void openVkUrl(place.groupUrl as string)}
              >
                Сообщество VK
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
