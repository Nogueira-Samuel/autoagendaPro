"""
Timezone Utilities

Funções auxiliares para manipulação de timezones e conversão de datas/horas.
Otimizado para uso com Google Calendar API e multi-tenant system.
"""

from datetime import datetime, date, time, timedelta
from typing import Any
import pytz


def get_timezone(tz_string: str = "America/Sao_Paulo") -> pytz.timezone:
    """
    Obtém objeto timezone do pytz.

    Args:
        tz_string: String do timezone (ex: "America/Sao_Paulo", "UTC")

    Returns:
        Objeto timezone do pytz

    Raises:
        pytz.exceptions.UnknownTimeZoneError: Se timezone inválido

    Examples:
        >>> tz = get_timezone("America/Sao_Paulo")
        >>> tz = get_timezone("America/New_York")
    """
    try:
        return pytz.timezone(tz_string)
    except pytz.exceptions.UnknownTimeZoneError:
        # Fallback para São Paulo se timezone inválido
        return pytz.timezone("America/Sao_Paulo")


def now_in_timezone(tz_string: str = "America/Sao_Paulo") -> datetime:
    """
    Obtém datetime atual no timezone especificado.

    Args:
        tz_string: String do timezone

    Returns:
        Datetime atual com timezone

    Examples:
        >>> now = now_in_timezone("America/Sao_Paulo")
        >>> now.tzinfo  # <DstTzInfo 'America/Sao_Paulo' ...>
    """
    tz = get_timezone(tz_string)
    return datetime.now(tz)


def localize_datetime(dt: datetime, tz_string: str) -> datetime:
    """
    Adiciona informação de timezone a um datetime naive.

    Args:
        dt: Datetime sem timezone (naive)
        tz_string: String do timezone a aplicar

    Returns:
        Datetime com timezone

    Raises:
        ValueError: Se datetime já tiver timezone

    Examples:
        >>> naive_dt = datetime(2024, 1, 15, 14, 30)
        >>> aware_dt = localize_datetime(naive_dt, "America/Sao_Paulo")
        >>> aware_dt.tzinfo  # <DstTzInfo 'America/Sao_Paulo' ...>
    """
    if dt.tzinfo is not None:
        raise ValueError("Datetime já possui timezone. Use convert_timezone() para converter.")

    tz = get_timezone(tz_string)
    return tz.localize(dt)


def convert_timezone(
    dt: datetime, from_tz: str, to_tz: str
) -> datetime:
    """
    Converte datetime de um timezone para outro.

    Args:
        dt: Datetime a converter (pode ser naive ou aware)
        from_tz: Timezone de origem
        to_tz: Timezone de destino

    Returns:
        Datetime no timezone de destino

    Examples:
        >>> dt_sp = datetime(2024, 1, 15, 14, 30)  # São Paulo
        >>> dt_ny = convert_timezone(dt_sp, "America/Sao_Paulo", "America/New_York")
        >>> # 14:30 em SP = 12:30 em NY (depende de DST)
    """
    # Se datetime é naive, localiza no timezone de origem
    if dt.tzinfo is None:
        dt = localize_datetime(dt, from_tz)

    # Converte para timezone de destino
    target_tz = get_timezone(to_tz)
    return dt.astimezone(target_tz)


def is_business_hours(
    dt: datetime, business_hours: dict, tz_string: str
) -> bool:
    """
    Verifica se datetime está dentro do horário comercial.

    Args:
        dt: Datetime a verificar
        business_hours: Dict com 'open' e 'close' (formato HH:MM)
        tz_string: Timezone do negócio

    Returns:
        True se dentro do horário comercial, False caso contrário

    Examples:
        >>> dt = datetime(2024, 1, 15, 14, 30)
        >>> hours = {'open': '09:00', 'close': '18:00', 'is_open': True}
        >>> is_business_hours(dt, hours, "America/Sao_Paulo")
        True
    """
    # Verifica se está aberto
    if not business_hours.get('is_open', True):
        return False

    # Converte para timezone do negócio se necessário
    if dt.tzinfo is None:
        dt = localize_datetime(dt, tz_string)
    else:
        dt = convert_timezone(dt, dt.tzinfo.zone, tz_string)

    # Parse horários de abertura e fechamento
    open_time = parse_time_string(business_hours.get('open', '00:00'))
    close_time = parse_time_string(business_hours.get('close', '23:59'))

    # Compara apenas o horário (ignora data)
    dt_time = dt.time()

    return open_time <= dt_time <= close_time


def parse_time_string(time_str: str) -> time:
    """
    Parse string de horário (HH:MM) para objeto time.

    Args:
        time_str: String no formato HH:MM

    Returns:
        Objeto time

    Raises:
        ValueError: Se formato inválido

    Examples:
        >>> t = parse_time_string("14:30")
        >>> t.hour, t.minute  # (14, 30)
    """
    try:
        hour, minute = map(int, time_str.split(':'))
        return time(hour=hour, minute=minute)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Formato de horário inválido: {time_str}. Use HH:MM") from e


def combine_date_time(
    date_obj: date, time_obj: time, tz_string: str
) -> datetime:
    """
    Combina date e time com timezone.

    Args:
        date_obj: Objeto date
        time_obj: Objeto time
        tz_string: String do timezone

    Returns:
        Datetime com timezone

    Examples:
        >>> d = date(2024, 1, 15)
        >>> t = time(14, 30)
        >>> dt = combine_date_time(d, t, "America/Sao_Paulo")
        >>> dt  # datetime(2024, 1, 15, 14, 30, tzinfo=...)
    """
    # Cria datetime naive
    naive_dt = datetime.combine(date_obj, time_obj)

    # Adiciona timezone
    return localize_datetime(naive_dt, tz_string)


def format_datetime_br(dt: datetime) -> str:
    """
    Formata datetime para exibição no formato brasileiro.

    Args:
        dt: Datetime a formatar

    Returns:
        String formatada (DD/MM/YYYY HH:MM)

    Examples:
        >>> dt = datetime(2024, 1, 15, 14, 30)
        >>> format_datetime_br(dt)
        '15/01/2024 14:30'
    """
    return dt.strftime("%d/%m/%Y %H:%M")


def format_date_br(d: date) -> str:
    """
    Formata date para exibição no formato brasileiro.

    Args:
        d: Date a formatar

    Returns:
        String formatada (DD/MM/YYYY)

    Examples:
        >>> d = date(2024, 1, 15)
        >>> format_date_br(d)
        '15/01/2024'
    """
    return d.strftime("%d/%m/%Y")


def format_time_br(t: time) -> str:
    """
    Formata time para exibição.

    Args:
        t: Time a formatar

    Returns:
        String formatada (HH:MM)

    Examples:
        >>> t = time(14, 30)
        >>> format_time_br(t)
        '14:30'
    """
    return t.strftime("%H:%M")


def get_weekday_name(dt: datetime, locale: str = "pt_BR") -> str:
    """
    Obtém nome do dia da semana em português.

    Args:
        dt: Datetime
        locale: Locale (padrão: pt_BR)

    Returns:
        Nome do dia em português (lowercase)

    Examples:
        >>> dt = datetime(2024, 1, 15)  # Segunda-feira
        >>> get_weekday_name(dt)
        'monday'
    """
    # Mapeamento de dias da semana
    weekday_map = {
        0: "monday",
        1: "tuesday",
        2: "wednesday",
        3: "thursday",
        4: "friday",
        5: "saturday",
        6: "sunday",
    }

    return weekday_map.get(dt.weekday(), "monday")


def get_weekday_name_pt(dt: datetime) -> str:
    """
    Obtém nome do dia da semana em português (display).

    Args:
        dt: Datetime

    Returns:
        Nome do dia em português

    Examples:
        >>> dt = datetime(2024, 1, 15)  # Segunda-feira
        >>> get_weekday_name_pt(dt)
        'Segunda-feira'
    """
    weekday_map_pt = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo",
    }

    return weekday_map_pt.get(dt.weekday(), "Segunda-feira")


def datetime_to_rfc3339(dt: datetime) -> str:
    """
    Converte datetime para formato RFC3339 (usado pelo Google Calendar).

    Args:
        dt: Datetime com timezone

    Returns:
        String RFC3339 (ex: "2024-01-15T14:30:00-03:00")

    Raises:
        ValueError: Se datetime não tiver timezone

    Examples:
        >>> dt = localize_datetime(datetime(2024, 1, 15, 14, 30), "America/Sao_Paulo")
        >>> rfc = datetime_to_rfc3339(dt)
        >>> rfc  # '2024-01-15T14:30:00-03:00'
    """
    if dt.tzinfo is None:
        raise ValueError("Datetime deve ter timezone para conversão RFC3339")

    return dt.isoformat()


def rfc3339_to_datetime(rfc_str: str) -> datetime:
    """
    Converte string RFC3339 para datetime.

    Args:
        rfc_str: String RFC3339

    Returns:
        Datetime com timezone

    Examples:
        >>> dt = rfc3339_to_datetime("2024-01-15T14:30:00-03:00")
        >>> dt.hour, dt.minute  # (14, 30)
    """
    return datetime.fromisoformat(rfc_str)


def add_minutes(dt: datetime, minutes: int) -> datetime:
    """
    Adiciona minutos a um datetime mantendo timezone.

    Args:
        dt: Datetime original
        minutes: Minutos a adicionar

    Returns:
        Novo datetime

    Examples:
        >>> dt = datetime(2024, 1, 15, 14, 30, tzinfo=pytz.UTC)
        >>> new_dt = add_minutes(dt, 60)
        >>> new_dt.hour  # 15
    """
    return dt + timedelta(minutes=minutes)


def get_date_range(
    start_date: date, days: int
) -> list[date]:
    """
    Gera lista de datas a partir de uma data inicial.

    Args:
        start_date: Data inicial
        days: Número de dias

    Returns:
        Lista de datas

    Examples:
        >>> start = date(2024, 1, 15)
        >>> dates = get_date_range(start, 7)
        >>> len(dates)  # 7
    """
    return [start_date + timedelta(days=i) for i in range(days)]


def is_same_day(dt1: datetime, dt2: datetime) -> bool:
    """
    Verifica se dois datetimes são no mesmo dia.

    Args:
        dt1: Primeiro datetime
        dt2: Segundo datetime

    Returns:
        True se mesmo dia

    Examples:
        >>> dt1 = datetime(2024, 1, 15, 10, 0)
        >>> dt2 = datetime(2024, 1, 15, 16, 0)
        >>> is_same_day(dt1, dt2)
        True
    """
    return dt1.date() == dt2.date()


def round_to_nearest_interval(
    dt: datetime, interval_minutes: int = 15
) -> datetime:
    """
    Arredonda datetime para o intervalo mais próximo.

    Args:
        dt: Datetime a arredondar
        interval_minutes: Intervalo em minutos (padrão: 15)

    Returns:
        Datetime arredondado

    Examples:
        >>> dt = datetime(2024, 1, 15, 14, 37)
        >>> rounded = round_to_nearest_interval(dt, 15)
        >>> rounded.minute  # 30 ou 45
    """
    # Arredonda para o intervalo mais próximo
    total_minutes = dt.hour * 60 + dt.minute
    rounded_minutes = round(total_minutes / interval_minutes) * interval_minutes

    new_hour = rounded_minutes // 60
    new_minute = rounded_minutes % 60

    return dt.replace(hour=new_hour, minute=new_minute, second=0, microsecond=0)


def get_start_of_day(dt: datetime, tz_string: str | None = None) -> datetime:
    """
    Obtém início do dia (00:00) para um datetime.

    Args:
        dt: Datetime
        tz_string: Timezone (opcional, usa timezone do dt se None)

    Returns:
        Datetime no início do dia

    Examples:
        >>> dt = datetime(2024, 1, 15, 14, 30)
        >>> start = get_start_of_day(dt, "America/Sao_Paulo")
        >>> start.hour, start.minute  # (0, 0)
    """
    if tz_string:
        tz = get_timezone(tz_string)
    elif dt.tzinfo:
        tz = dt.tzinfo
    else:
        tz = get_timezone("America/Sao_Paulo")

    # Cria datetime no início do dia
    start = datetime.combine(dt.date(), time(0, 0))

    if isinstance(tz, pytz.tzinfo.BaseTzInfo):
        return tz.localize(start)
    else:
        return start.replace(tzinfo=tz)


def get_end_of_day(dt: datetime, tz_string: str | None = None) -> datetime:
    """
    Obtém fim do dia (23:59:59) para um datetime.

    Args:
        dt: Datetime
        tz_string: Timezone (opcional)

    Returns:
        Datetime no fim do dia

    Examples:
        >>> dt = datetime(2024, 1, 15, 14, 30)
        >>> end = get_end_of_day(dt, "America/Sao_Paulo")
        >>> end.hour, end.minute  # (23, 59)
    """
    if tz_string:
        tz = get_timezone(tz_string)
    elif dt.tzinfo:
        tz = dt.tzinfo
    else:
        tz = get_timezone("America/Sao_Paulo")

    # Cria datetime no fim do dia
    end = datetime.combine(dt.date(), time(23, 59, 59))

    if isinstance(tz, pytz.tzinfo.BaseTzInfo):
        return tz.localize(end)
    else:
        return end.replace(tzinfo=tz)
