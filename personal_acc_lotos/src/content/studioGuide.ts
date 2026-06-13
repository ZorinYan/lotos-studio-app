export type StudioContactTopic =
  | 'renew'
  | 'freeze'
  | 'reschedule'
  | 'payment'
  | 'general'

export type StudioContactContext = {
  clientName?: string | null
  phoneDisplay?: string | null
  abonementTitle?: string | null
  abonementRemaining?: number | null
  recordService?: string | null
  recordDatetime?: string | null
}

export type FaqItem = {
  id: string
  question: string
  answer: string
}

export const STUDIO_FAQ: FaqItem[] = [
  {
    id: 'cancel',
    question: 'За сколько можно отменить запись?',
    answer:
      'Отмените запись в приложении заранее — как минимум за несколько часов до начала занятия. ' +
      'Если занятие уже скоро, напишите администратору в сообщения сообщества.',
  },
  {
    id: 'bring',
    question: 'Что взять с собой?',
    answer:
      'Удобную одежду для практики, сменную обувь или носки, полотенце и бутылку воды. ' +
      'Коврик и реквизит обычно есть в студии — уточните у администратора, если сомневаетесь.',
  },
  {
    id: 'trial',
    question: 'Как работает пробное занятие?',
    answer:
      'Новые клиенты могут записаться на пробное занятие через расписание — цена отображается в карточке. ' +
      'Приходите за 10 минут до начала, чтобы спокойно переодеться и познакомиться с пространством.',
  },
  {
    id: 'freeze',
    question: 'Можно ли заморозить абонемент?',
    answer:
      'Да, заморозка оформляется через администратора студии. Напишите нам в VK с темой «Заморозить абонемент» — ' +
      'укажите срок и причину, мы ответим в рабочее время.',
  },
  {
    id: 'route',
    question: 'Как добраться и где парковка?',
    answer:
      'Адрес и карта — в блоке «Как нас найти» на главной. Откройте маршрут в Яндекс.Картах кнопкой «Открыть на карте». ' +
      'По парковке уточняйте у администратора — подскажем ближайшие варианты.',
  },
]

export const FIRST_VISIT_TIPS = [
  {
    title: 'Приходите за 10 минут',
    text: 'Будет время переодеться, познакомиться с пространством и настроиться на практику.',
  },
  {
    title: 'Удобная одежда',
    text: 'Выберите комфортную форму, в которой легко двигаться. Обувь можно снять в зале.',
  },
  {
    title: 'Вход и раздевалка',
    text: 'Администратор встретит у входа или подскажет, куда пройти. Раздевалка и душ — на месте.',
  },
]

export const STUDIO_CONTACT_TOPICS: Array<{
  id: StudioContactTopic
  label: string
  subject: string
}> = [
  { id: 'renew', label: 'Продлить абонемент', subject: 'Продление абонемента' },
  { id: 'freeze', label: 'Заморозить абонемент', subject: 'Заморозка абонемента' },
  { id: 'reschedule', label: 'Перенести индивидуальное', subject: 'Перенос индивидуального занятия' },
  { id: 'payment', label: 'Вопрос по оплате', subject: 'Вопрос по оплате' },
  { id: 'general', label: 'Другой вопрос', subject: 'Вопрос в студию Lotos' },
]

export function buildStudioContactMessage(
  topic: StudioContactTopic,
  context: StudioContactContext,
): string {
  const meta = STUDIO_CONTACT_TOPICS.find((item) => item.id === topic)
  const lines = [
    meta?.subject ?? 'Сообщение из приложения Lotos',
    '',
  ]

  if (context.clientName) {
    lines.push(`Имя: ${context.clientName}`)
  }
  if (context.phoneDisplay) {
    lines.push(`Телефон: ${context.phoneDisplay}`)
  }
  if (context.abonementTitle) {
    const remaining =
      context.abonementRemaining != null
        ? ` (осталось ${context.abonementRemaining})`
        : ''
    lines.push(`Абонемент: ${context.abonementTitle}${remaining}`)
  }
  if (context.recordService && context.recordDatetime) {
    lines.push(`Запись: ${context.recordService} · ${context.recordDatetime}`)
  }

  lines.push('', 'Текст обращения:', '')
  return lines.join('\n')
}
