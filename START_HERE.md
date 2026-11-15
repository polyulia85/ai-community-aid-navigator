# Community Aid Navigator с Supervisor

## Запуск

Распакуйте ZIP. В терминале откройте папку с `agents.json` и запустите приложение на Python 3.11 или новее.

```sh
python3 -m app_layer.server
```

Откройте [Navigator](http://127.0.0.1:8765/). Если порт занят, запустите `python3 -m app_layer.server --port 18765` и откройте [Navigator на порту 18765](http://127.0.0.1:18765/).

Для проверки в **Conversation** используйте вымышленную историю.

> I live in Sacramento ZIP code 95823 with my two children. I lost my job. I need food this week and help paying $1,450 rent.

Ответы на уточнения в этом сценарии:

- `My household gross monthly income is $900.`
- `There are 3 people in my household.`
- `Yes` на вопрос о договоре аренды и `No` на вопрос о письменном уведомлении.
- `400` на вопрос о недостающей сумме и `2026-12-01` на вопрос о сроке оплаты.
- `Yes` на вопрос, закончится ли еда сегодня или завтра. На вопрос о доступных сейчас деньгах для этого теста ответьте `20`.

В **Situation Summary** проверьте факты и нажмите **Confirm Information**. Откройте **Action Plan**, проверьте **Start here** и переключайте **Food Bank**, **CalFresh** и **Housing** через меню плана. Выберите **CalFresh**, затем в **Housing** откройте **Sacramento Coordinated Access System (2-1-1, press 8)**, чтобы проверить условия, документы, инструкции, контакты и источники. **My Case** показывает подтверждённые сведения и прогресс.

Состояние сохраняется в текущей вкладке и переживает перезагрузку страницы. Кнопка **Start a new case** в **My Case** очищает сохранённый кейс. Используйте вымышленные данные. Для локального запуска ключи watsonx.ai и IBM Bob не нужны.

## Проверки

```sh
python3 -m unittest discover -q
```

В отдельном терминале при работающем сервере можно запустить браузерную проверку. Она требует Node.js 22 и Chrome. Второй аргумент позволяет указать путь к Chrome, если он установлен в другом месте.

```sh
node tools/check_app_browser.mjs http://127.0.0.1:8765
```

Результаты, происхождение сборки и границы проверки описаны в [отчёте](INTEGRATION_REPORT.md).
