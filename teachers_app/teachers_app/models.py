# -*- coding: utf-8 -*-

import re
import time
import datetime, math, calendar as calendar_origin
from django.db import models
from django.utils.functional import cached_property
from django.utils.timezone import utc
from django.contrib.auth.models import User as UserOrigin, UserManager
from project.settings import FILE_STORAGE


from application.utils.date_api import get_count_of_weekdays_per_interval, get_week_days_names, MONTH_PARENT_FORM, WEEK
from application.utils.phones import get_string_val

calendar = calendar_origin.Calendar()

class User(UserOrigin):

    def __unicode__(self):
        return '%s %s' % (self.last_name, self.first_name)

    objects = UserManager
    rights = models.ManyToManyField("UserRights", verbose_name="Права пользователя")

    u"""
    !!! deprecated !!!
    about = models.TextField(verbose_name=u'Описание преподавателя', null=True, blank=True)
    photo = models.FileField(upload_to=FILE_STORAGE, null=True, blank=True, verbose_name=u'Фото')
    video = models.CharField(max_length=100, null=True, blank=True, verbose_name=u'Видео')

    @property
    def photo_file(self):
        return self.photo.name.split('/')[-1] if self.photo else None
    """

    def __short_json__(self):
        return dict(
            first_name=self.first_name,
            last_name=self.last_name
        )

    def __json__(self):
        return dict(
            first_name=self.first_name,
            last_name=self.last_name,
            about=self.about,
            photo=self.photo.url,
            video=self.video
        )

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Преподаватель'
        verbose_name_plural = u'Преподаватели'


class UserRights(models.Model):
    u"""
    ORM - Права пользователя в системе
    """

    string_code = models.CharField(max_length=10, verbose_name=u"Код")
    name = models.CharField(max_length=50, verbose_name=u"Наименование")

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Права пользователея'
        verbose_name_plural = u'Права пользователей'


class Dances(models.Model):
    """
    ORM-модель "Танец"
    """

    name = models.CharField(max_length=50, verbose_name=u'Наименование')

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Танцевальное направление'
        verbose_name_plural = u'Танцевальные направления'


class GroupLevels(models.Model):
    """
    ORM-модель уровни групп
    """
    name = models.CharField(max_length=50, verbose_name=u'Наименование')
    string_code = models.CharField(max_length=50, verbose_name=u'Код')

    u"""
    course_details = models.TextField(null=True, blank=True, verbose_name=u'Подробности о курсе')
    course_results = models.TextField(null=True, blank=True, verbose_name=u'Результаты прохождения курса')
    """

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Уровень группы'
        verbose_name_plural = u'Уровни групп'


class DanceHalls(models.Model):
    """
    Зал
    """

    name = models.CharField(max_length=50, verbose_name=u'Наименование', null=True, blank=True)
    station = models.CharField(max_length=50, verbose_name=u'Станция метро', null=True, blank=True)
    prise = models.PositiveIntegerField(verbose_name=u'Цена')
    address = models.CharField(max_length=200, verbose_name=u'Адрес', null=True, blank=True)

    u"""
    time_to_come = models.PositiveIntegerField(verbose_name=u'Минуты от метро', null=True, blank=True)
    lon = models.FloatField(verbose_name=u'Широта', null=True, blank=True)
    lat = models.FloatField(verbose_name=u'Долгота', null=True, blank=True)
    about = models.TextField(verbose_name=u'Описание преподавателя', null=True, blank=True)
    map = models.FileField(upload_to=FILE_STORAGE, null=True, blank=True)
    photo1 = models.FileField(upload_to=FILE_STORAGE, null=True, blank=True)
    photo2 = models.FileField(upload_to=FILE_STORAGE, null=True, blank=True)
    photo3 = models.FileField(upload_to=FILE_STORAGE, null=True, blank=True)

    def get_filename(self, field):
        return field.name.split('/')[-1] if field else None

    @property
    def map_filename(self):
        return self.get_filename(self.map)

    @property
    def p1_filename(self):
        return self.get_filename(self.photo1)

    @property
    def p2_filename(self):
        return self.get_filename(self.photo2)

    @property
    def p3_filename(self):
        return self.get_filename(self.photo3)
    """

    def __unicode__(self):
        return self.name if self.name else u''

    def __json__(self):
        return dict(
            id=self.pk,
            name=self.name,
            station=self.station,
            prise=self.prise,
            address=self.address,
           # time_to_come=self.time_to_come,
           # lon=self.lon,
           # lat=self.lat
        )

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Зал'
        verbose_name_plural = u'Залы'


class AllGroupManager(models.Manager):
    def owner(self, user):
        return self.get_queryset().filter(models.Q(teacher_leader=user) | models.Q(teacher_follower=user))

    def exclude_owner(self, user):
        return self.get_queryset().exclude(models.Q(teacher_leader=user) | models.Q(teacher_follower=user))


class OpenedGroupManager(BaseGroupManager):
    def get_queryset(self):
        return super(OpenedGroupManager, self).get_queryset().filter(models.Q(end_date__isnull=True) | models.Q(end_date__gte=datetime.datetime.now().date()))


class ClosedGroupsManager(BaseGroupManager):
    def get_queryset(self):
        return super(ClosedGroupsManager, self).get_queryset().filter(end_date__lt=datetime.datetime.now().date())


class Group(models.Model):

    u"""
    ORM - Группa
    """

    all = AllGroupManager()
    opened = OpenedGroupManager()
    closed = ClosedGroupsManager()

    name = models.CharField(max_length=100, verbose_name=u'Название группы')
    use_callendar = models.BooleanField(verbose_name=u'Автоматический расчет дней по каллендарю')
    dance = models.ForeignKey(Dances, null=True, blank=True, verbose_name=u'Направление')
    level = models.ForeignKey(GroupLevels, null=True, blank=True, verbose_name=u'Уровень')
    start_date = models.DateField(verbose_name=u'Дата начала группы')
    end_date = models.DateField(verbose_name=u'Дата окончания группы', null=True, blank=True, default=None)
    time = models.TimeField(verbose_name=u'Время начала занятия', null=True, blank=True, default=None)
    end_time = models.TimeField(verbose_name=u'Время окончания занятия', null=True, blank=True, default=None)
    teachers = models.ManyToManyField(User, verbose_name=u'Преподаватели', null=True, blank=True, related_name=u'allteachers')
    _days = models.CommaSeparatedIntegerField(max_length=13, verbose_name=u'Дни')
    available_passes = models.ManyToManyField('PassTypes', verbose_name=u'Абонементы для преподавателей', related_name=u'avp', null=True, blank=True)
    external_passes = models.ManyToManyField('PassTypes', verbose_name=u'Абонементы для показа на внешних сайтах', related_name=u'exp', null=True, blank=True)
    dance_hall = models.ForeignKey(DanceHalls, verbose_name=u'Зал')
    updates = models.CommaSeparatedIntegerField(max_length=200, verbose_name=u'Донаборы в группу', null=True, blank=True)
    lending_message = models.CharField(max_length=100, verbose_name=u'Сообщение в шапке лендинга', null=True, blank=True)
    free_placees = models.IntegerField(verbose_name=u'Общее кол-во мест в группе', null=True, blank=True)
    duration = models.IntegerField(verbose_name=u'Продолжительность курса', null=True, blank=True)
    course_details = models.TextField(verbose_name=u'Подробности о группе', null=True, blank=True)
    course_results = models.TextField(verbose_name=u'Результаты после прохождения', null=True, blank=True)

    @staticmethod
    def date_repr(dt):
        return u'%d %s %d' % (dt.day, MONTH_PARENT_FORM[dt.month].lower(), dt.year)

    @property
    def is_opened(self):
        now_date = datetime.datetime.now().date()
        return self.end_date is None or self.end_date >= now_date

    def nearest_update(self):
        if not self.updates:
            return None

        now = time.mktime(datetime.datetime.now().date().timetuple())
        updates = [
            datetime.datetime.fromtimestamp(i).date()
            for i in map(int, self.updates.split(','))
            if i >= now
        ]

        past_updates = [
            datetime.datetime.fromtimestamp(i).date()
            for i in map(int, self.updates.split(','))
            if i < now
        ]

        if len(updates) > 0:
            return sorted(updates)[0]
        elif len(past_updates) > 0:
            return sorted(past_updates)[-1]
        else:
            return None

    @property
    def days(self):
        return get_week_days_names(self._days.split(','))

    @property
    def days_nums(self):
        return map(int,self._days.split(','))

    @property
    def start_date_str(self):
        return self.date_repr(self.start_date)

    @property
    def end_date_str(self):
        return self.date_repr(self.end_date)

    @property
    def last_lesson(self):
        now = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        _from = datetime.datetime.combine(self.start_date, datetime.datetime.min.time())
        cnt = get_count_of_weekdays_per_interval(self.days, _from, now) + 1
        return self.start_date if now <= _from else filter(lambda x: x <= now, self.get_calendar(cnt))[-1].date()

    @property
    def teachers_str(self):
        if self.teacher_leader and self.teacher_follower:
            return u'%s - %s' % (self.teacher_leader, self.teacher_follower)
        else:
            return self.teacher_leader or self.teacher_follower

    def get_calendar(self, count, date_from=None, clean=True):
        start_date = date_from if date_from else self.start_date
        days = calendar.itermonthdays2(start_date.year, start_date.month)

        cur_month_days = map(
            lambda _d: datetime.datetime(start_date.year, start_date.month, _d[0]),
            filter(lambda day: day[0] and day[0] >= start_date.day and day[1] in self.days_nums, days)
        )

        try:
            canceled_lessons = CanceledLessons.objects.filter(group=self, date__gte=start_date).values_list('date', flat=True)

        except CanceledLessons.DoesNotExist:
            canceled_lessons = []

        if clean:
            cur_month_days = filter(lambda day: day.date() not in canceled_lessons, cur_month_days)

        if len(cur_month_days) < count:
            next_month = start_date.month + 1 if start_date.month < 12 else 1
            next_year = start_date.year if start_date.month < 12 else start_date.year + 1

            cur_month_days += self.get_calendar(
                count - len(cur_month_days),
                datetime.datetime(next_year, next_month, 1),
                clean=clean
            )

        res = cur_month_days[:count]

        if not clean:

            _res = []

            for r in res:
                _res.append(
                    {'date': r, 'canceled': r.date() in canceled_lessons} if not isinstance(r, dict) else r
                )

            res = _res

        return res

    @property
    def start_datetime(self):
        return datetime.datetime.combine(self.start_date, datetime.datetime.min.time())

    @property
    def end_datetime(self):
        return datetime.datetime.combine(self.end_date, datetime.datetime.min.time()) if self.end_date else None

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):

        if self.end_date is None:
            prev_group = Groups.objects.filter(
                dance_hall=self.dance_hall,
                time=self.time,
                _days=self._days,
                start_date__lt=self.start_date,
            ).exclude(pk=self.pk).order_by('start_date').last()

            if prev_group and prev_group.end_date is None:
                prev_group.end_date = self.start_date
                prev_group.save()

        super(Groups, self).save(force_insert, force_update, using, update_fields)

    @property
    def time_repr(self):
        return str(self.time or '')[0:-3]

    def __json__(self):
        return dict(
            name=self.name,
            start_date=self.start_date.strftime('%d.%m.%Y') if self.start_date else u'',
            end_date=self.end_date.strftime('%d.%m.%Y') if self.end_date else u'',
            time=self.time_repr,
            teacher_leader=self.teacher_leader.__json__() if self.teacher_leader else {},
            teacher_follower=self.teacher_follower.__json__() if self.teacher_follower else {},
            is_opened=self.is_opened,
            is_settable=self.is_settable,
            days=self.days,
            available_passes=self.available_passes,
            dance_hall=self.dance_hall.__json__()
        )

    def __unicode__(self):
        today = datetime.datetime.now().date()

        teachers = ', '.join(map(lambda t: t.last_name, self.teachers.all()))
        days = '-'.join(self.days)

        if self.start_date > today:
            return u'%s c %s %s %s %s' % (self.name, self.start_date_str, teachers, days, self.time_repr)

        elif not self.is_opened:
            if self.start_date == self.end_date:
                return u'%s %s %s %s %s - ЗАКРЫТА' % (self.name, self.start_date_str, teachers, days, self.time_repr)
            else:
                return u'%s c %s по %s %s %s %s - ЗАКРЫТА' % (self.name, self.start_date_str, self.end_date_str, teachers, days, self.time_repr)

        else:
                return u'%s - %s - %s %s' % (self.name, teachers, days, self.time_repr)

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Группу'
        verbose_name_plural = u'Группы'


class BonusClasses(models.Model):

    date = models.DateField(verbose_name=u'Дата')
    time = models.TimeField(verbose_name=u'Время начала', null=True, blank=True)
    end_time = models.TimeField(verbose_name=u'Время окончания', null=True, blank=True)
    hall = models.ForeignKey(DanceHalls, verbose_name=u'Зал')
    teachers = models.ManyToManyField('User', verbose_name=u'Преподаватели')
    can_edit = models.BooleanField(verbose_name=u'Открыт для редактирования преподавателями', default=True)
    available_passes = models.ManyToManyField('PassTypes', verbose_name=u'Доступные абонементы', null=True, blank=True)
    available_groups = models.ManyToManyField('Groups', verbose_name=u'Доступные группы', null=True, blank=True)

    def repr_short(self):
        return u'%s %s' % (self.date.strftime('%d.%m.%Y'), self.hall.name)

    @property
    def begin_datetime(self):
        return datetime.datetime.combine(self.date, self.time)

    @property
    def end_datetime(self):
        return datetime.datetime.combine(self.date, self.end_time)


    @property
    def repr(self):
        return self.repr_short()

    @property
    def teachers_str(self):
        return ', '.join(map(str, self.teachers.all()))

    def __unicode__(self):
        return u'%s %s %s %s' % (
            self.date.strftime('%d.%m.%Y'),
            self.hall.station,
            self.teacher_leader.last_name if self.teacher_leader else u'',
            self.teacher_follower.last_name if self.teacher_follower else u''
        )

    class Meta:
        unique_together = ('date', 'hall')
        app_label = u'teacher_app'
        verbose_name = u'Мастер-класс'
        verbose_name_plural = u'Мастер-классы'


class CanceledLessons(models.Model):
    group = models.ForeignKey(Groups)
    date = models.DateField(verbose_name=u'Дата отмененного урока')

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Отмененное занятие'
        verbose_name_plural = u'Отмененные занятия'


class Students(models.Model):

    u"""
    Ученики
    """

    first_name = models.CharField(max_length=30, verbose_name=u'Фамилия')
    last_name = models.CharField(max_length=30, verbose_name=u'Имя')
    father_name = models.CharField(max_length=30, verbose_name=u'Отчество', null=True, blank=True)
    phone = models.CharField(verbose_name=u'Телефон', max_length=20)
    e_mail = models.CharField(max_length=30, verbose_name=u'e-mail', null=True, blank=True)
    org = models.BooleanField(verbose_name=u'Орг', default=False)
    is_deleted = models.BooleanField(verbose_name=u'Удален', default=False)

    def __json__(self):
        return dict(
            id=self.pk,
            first_name=self.first_name,
            last_name=self.last_name,
            phone=self.str_phone,
            raw_phone=self.phone,
            e_mail=self.e_mail,
            org=self.org
        )

    def __unicode__(self):
        return u'%s %s.%s' % (self.first_name, self.last_name[0].upper(), self.father_name[0].upper() if self.father_name else '')

    @property
    def str_phone(self):
        return get_string_val(self.phone)

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Ученик'
        verbose_name_plural = u'Ученики'


class Debts(models.Model):
    u"""
    Хранилищи записей о долгах
    """

    date = models.DateField(verbose_name=u'Дата')
    student = models.ForeignKey(Students)
    group = models.ForeignKey(Groups)
    val = models.FloatField(verbose_name=u'Сумма')

    def __unicode__(self):
        '%s - %s - %s' % (
            self.date.strftime('%d.%m.%Y') if self.date else '',
            self.student.__unicode__(),
            self.group.__unicode__()
        )

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Долг'
        verbose_name_plural = u'Долги'


class Comments(models.Model):
    u"""
    Хранилице коментов
    """

    add_date = models.DateTimeField(verbose_name=u'Дата добавления')
    student = models.ForeignKey(Students)
    group = models.ForeignKey(Groups, null=True, blank=True)
    bonus_class = models.ForeignKey(BonusClasses, null=True, blank=True)
    text = models.TextField(max_length=100, verbose_name=u'Текст коментария')

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Коментарий'
        verbose_name_plural = u'Коментарии'


class PassTypes(models.Model):

    u"""
    Типы Абонементов
    """

    name = models.CharField(max_length=100, verbose_name=u'Наименование')
    prise = models.PositiveIntegerField(verbose_name=u'Цена')
    lessons = models.PositiveIntegerField(verbose_name=u'Количество занятий')
    skips = models.PositiveIntegerField(verbose_name=u'Количество пропусков', null=True, blank=True)
    color = models.CharField(verbose_name=u'Цвет', max_length=7, null=True, blank=True)
    one_group_pass = models.BooleanField(verbose_name=u'Одна группа', default=True)
    sequence = models.PositiveIntegerField(verbose_name=u'Порядковый номер', null=True, blank=True)
    shown_value = models.CharField(verbose_name=u'Отображаемое значение(если пустое - показывается цена за занятие)', null=True, blank=True, max_length=30)

    def __unicode__(self):
        return u'%s - %s (%dр.)' % (str(self.sequence), self.name, self.prise)

    def __json__(self):
        return dict(
            name=self.name,
            prise=self.prise,
            lessons=self.lessons,
            skips=self.skips,
            color=self.color,
            oneGroupPass=self.one_group_pass
        )

    def save(self, *args, **kwargs):

        try:
            max_seq = PassTypes.objects.all().aggregate(models.Max('sequence'))['sequence__max'] or 0

        except PassTypes.DoesNotExist:
            max_seq = 0

        if not self.sequence or self.sequence > max_seq:
            self.sequence = max_seq + 1

        else:

            try:
                prev_seq = PassTypes.objects.get(id=self.id).sequence

            except PassTypes.DoesNotExist:
                prev_seq = None

            if prev_seq != self.sequence:
                if prev_seq and self.sequence > prev_seq:
                    _type = PassTypes.objects.filter(sequence__gt=prev_seq).order_by('sequence').first()
                    _type.sequence = prev_seq
                    super(PassTypes, _type).save()

                else:
                    _seq = self.sequence + 1
                    for _type in PassTypes.objects.filter(sequence__gte=self.sequence).exclude(id=self.id).order_by('sequence'):
                        _type.sequence = _seq
                        _seq += 1

                        super(PassTypes, _type).save()

        super(PassTypes, self).save(*args, **kwargs)

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Тип абонемента'
        verbose_name_plural = u'Типы абонементов'


class GroupList(models.Model):

    u"""
    Список группы
    """

    group = models.ForeignKey(Groups, verbose_name=u'Группа')
    student = models.ForeignKey(Students, verbose_name=u'Ученик')
    active = models.BooleanField(verbose_name=u'Ссылка активна', default=True)
    last_update = models.DateField(verbose_name=u'Последнее обновление записи', auto_now=True)

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Список группы'
        verbose_name_plural = u'Списки групп'
        unique_together = ('group', 'student')


class Passes(models.Model):

    u"""
    Абонементы
    """

    student = models.ForeignKey(Students, verbose_name=u'Ученик')
    # group = models.ManyToManyField(Groups, verbose_name=u'Группа', null=True, blank=True)
    group = models.ForeignKey(Groups, verbose_name=u'Группа', null=True, blank=True)
    start_date = models.DateField(verbose_name=u'Начало действия абонемента', null=True, blank=True)
    end_date = models.DateField(verbose_name=u'Окончание действия абонемента', null=True, blank=True)
    pass_type = models.ForeignKey(PassTypes, verbose_name=u'Абонемент', null=True, blank=True, default=None)
    lessons = models.PositiveIntegerField(verbose_name=u'Количество оставшихся занятий')
    skips = models.PositiveIntegerField(verbose_name=u'Количество оставшихся пропусков', null=True, blank=True)
    frozen_date = models.DateField(verbose_name=u'Дата окончания заморозки', null=True, blank=True)
    lessons_origin = models.PositiveIntegerField(verbose_name=u'Количество изначально заданных занятий')
    skips_origin = models.PositiveIntegerField(verbose_name=u'Количество изначально заданных пропусков', null=True, blank=True)
    opener = models.ForeignKey(User, null=True, blank=True)
    creation_date = models.DateField(verbose_name=u'Дата содания(оплаты абонемента)', null=True, blank=True, auto_now=True)
    bonus_class = models.ForeignKey(BonusClasses, verbose_name=u'Мастер-класс', null=True, blank=True)

    @property
    def one_group_pass(self):
        return self.pass_type.one_group_pass

    @property
    def shown_value(self):
        return self.pass_type.shown_value

    @property
    def date(self):
        return self.frozen_date or self.start_date

    def get_lessons_before_date(self, date):
        return Lessons.objects.filter(group_pass=self, date__lt=date)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.lessons is None:
            self.lessons = self.pass_type.lessons
        if self.skips in [None, '']:
            self.skips = self.pass_type.skips if isinstance(self.pass_type.skips, int) else None

        if self.lessons_origin is None:
            self.lessons_origin = self.pass_type.lessons

        if self.skips_origin in [None, '']:
            self.skips_origin = self.pass_type.skips if isinstance(self.pass_type.skips, int) else None

        super(Passes, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    @property
    def color(self):
        return self.pass_type.color

    @property
    def one_lesson_prise(self):
        return round(float(self.pass_type.prise) / self.pass_type.lessons, 2)

    @cached_property
    def _lessons(self):
        return list(Lessons.objects.filter(group_pass=self).order_by('date'))

    @property
    def first_lesson_date(self):
        return self._lessons[0]

    @property
    def last_lesson_date(self):
        return self._lessons[-1]

    def __json__(self):
        return dict(
            id=self.id,
            student=self.student.id,
            group=self.group.id,
            start_date=self.start_date.isoformat(),
            end_date=self.end_date,
            pass_type=self.pass_type.__json__(),
            lessons=self.lessons,
            skips=self.skips,
            color=self.color
        )

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Абонемент'
        verbose_name_plural = u'Абонементы'


class Lessons(models.Model):

    u"""
    Посещения занятий
    """

    STATUSES = {
        'not_processed': 0,
        'attended': 1,
        'not_attended': 2,
        'frozen': 3,
        'moved': 4,
        'written_off': 5
    }
    STATUSES_RUS = {
        'not_processed': u'не обработано',
        'attended': u'был(а)',
        'not_attended': u'не был(а)',
        'frozen': u'заморожен',
        'moved': u'пропуск',
        'written_off': u'списан'
    }
    DEFAULT_STATUS = STATUSES['not_processed']

    date = models.DateField(verbose_name=u'Дата занятия')
    group = models.ForeignKey(Groups, verbose_name=u'Группа')
    student = models.ForeignKey(Students, verbose_name=u'Учение')
    group_pass = models.ForeignKey(Passes, verbose_name=u'Абонемент', related_name=u'lesson_group_pass')
    status = models.IntegerField(verbose_name=u'Статус занятия', choices=[(val, key) for key, val in STATUSES.iteritems()], default=DEFAULT_STATUS)

    @property
    def sign(self):

        if self.status == Lessons.STATUSES['not_processed']:
            return ''
        elif self.status == Lessons.STATUSES['moved']:
            return Lessons.STATUSES_RUS['moved']
        elif self.status == Lessons.STATUSES['attended']:
            return self.group_pass.shown_value or str(self.prise()) + 'р'
        else:
            return '--' + self.group_pass.shown_value if self.group_pass.shown_value else self.prise() * -1

    @property
    def rus(self):
        rev_status = {val: key for key, val in self.STATUSES.iteritems()}
        return self.STATUSES_RUS[rev_status[self.status]]

    def prise(self):
        return self.group_pass.one_lesson_prise

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        now = datetime.datetime.now().date()
        try:
            compared_date = self.date.date()
        except AttributeError:
            compared_date = self.date

        if compared_date > now:
            self.status = Lessons.STATUSES['not_processed']

        super(Lessons, self).save(force_insert, force_update, using, update_fields)

    @cached_property
    def is_first_in_pass(self):
        #first_lesson = Lessons.objects.filter(group_pass=self.group_pass).earliest('date')
        return self.group_pass.start_date == self.date

    @cached_property
    def is_last_in_pass(self):
        last_lesson = Lessons.objects.filter(group_pass=self.group_pass).latest('date')
        return last_lesson.date == self.date

    def __unicode__(self):
        return self.date.strftime('%d.%m.%Y')

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Журнал посещения'


class SampoPayments(models.Model):

    date = models.DateTimeField(verbose_name=u'Время оплаты')
    staff = models.ForeignKey(User, verbose_name=u'Администратор САМПО')
    people_count = models.PositiveIntegerField(verbose_name=u'Количество людей')
    money = models.IntegerField(verbose_name=u'Сумма')
    comment = models.CharField(verbose_name=u'Коментарий', max_length=50, null=True, blank=True)

    def __str__(self):
        return '%s %s %d' % (self.date.strftime('%d.%m.%Y %H:%M'), self.staff, self.money)

    def __unicode__(self):
        return u'%s %s %d' % (self.date.strftime('%d.%m.%Y %H:%M'), self.staff, self.money)

    def __json__(self):
        return dict(
            date=self.date.strftime('%d.%m.%Y %H:%M'),
            staff=self.staff.__short_json__(),
            people_count=self.people_count,
            money=self.money,
            comment=self.comment
        )

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Оплата сампо'


class SampoPasses(models.Model):

    name = models.TextField(verbose_name=u'Имя')
    surname = models.TextField(verbose_name=u'фамилия')
    payment = models.ForeignKey(SampoPayments, verbose_name=u'Оплата абонемента')

    def __str__(self):
        return '%s %s %s' % (self.surname, self.name, self.payment)

    def __unicode__(self):
        return u'%s %s %s' % (self.name, self.surname, self.payment)

    def __json__(self):

        return dict(
            id=self.pk,
            name=self.name,
            surname=self.surname,
            payment=self.payment.__json__()
        )

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Абонементы САМПО'


class SampoPassUsage(models.Model):

    sampo_pass = models.ForeignKey(SampoPasses, verbose_name=u'Абонемент')
    date = models.DateTimeField(verbose_name=u'Время')

    class Meta:
        app_label = u'teacher_app'
        verbose_name = u'Отметки о посещении сампо'


class HtmlPaymentsTypes(object):

    ADD = 'text-success'
    WRITE_OFF = 'text-error'
    DEFAULT = ''


class Log(models.Model):

    date = models.DateTimeField(verbose_name=u'Время записи', auto_now=True)
    msg = models.TextField(verbose_name=u'Сообщение', max_length=1000)

    def __unicode__(self):
        return '%s - %s' % (self.date.strftime('%d.%m.%Y %H:%M:%S'), self.msg)


class SampoPrises(models.Model):
    prise = models.PositiveIntegerField(verbose_name=u'Сумма')
    date_from = models.DateField(verbose_name=u'Дата начала действия')
    date_to = models.DateField(verbose_name=u'Дата окончания действия', null=True, blank=True)

    def __unicode__(self):
        return u'c %s по %s (%d)' % (self.date_from.strftime('%d.%m.%Y'), self.date_to.strftime('%d.%m.%Y') if self.date_to else u'не ограничено', self.prise)

    class Meta:
        unique_together = ('date_from', 'date_to')
        app_label = u'teacher_app'
        verbose_name = u'Цены на сампо'
        verbose_name_plural= u'Цены на сампо'


class BonusClassList(models.Model):

    group = models.ForeignKey(BonusClasses)
    student = models.ForeignKey(Students)
    attendance = models.BooleanField(verbose_name=u'Присутствие', default=False)
    group_pass = models.ForeignKey(Passes, null=True, blank=True)
    active = models.BooleanField(verbose_name=u'Ссылка активна', default=True)

    def update(self, **kwargs):
        for key, val in kwargs.iteritems():
            setattr(self, key, val)
        self.save()

    class Meta:
        unique_together = ('group', 'student')
        app_label = u'teacher_app'
