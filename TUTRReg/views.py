from django.shortcuts import render, get_object_or_404
from django.http import Http404, HttpResponseRedirect
from django.views import generic, View
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Q, Sum

from .models import Event, Session, Class, Course, Attendance, Person, User, Degree, Major
from .forms import EventForm, ClassForm, PersonForm, AttendanceForm, AttendanceFormSet, RegistrationForm
from datetime import datetime
# Create your views here.


def register_user(response):
    if response.method == "POST":
        form = RegistrationForm(response.POST)
        if form.is_valid():
            form.save()
        return HttpResponseRedirect(reverse('/'))
    else:
        form = RegistrationForm()

    return render(response, "TUTRReg/register.html", {"form":form})


def register(request, *args, **kwargs):
    if request.POST:
        person = Person.objects.get(pk=kwargs['person_id'])
        session = Session.objects.get(pk=kwargs['session_id'])
        registration = Attendance.objects.create(session_id=session, person_id=person, attended=False, passed=False)
        event = session.pk
        registration.save()

    return HttpResponseRedirect(reverse('TUTRReg:attendance', args=(event,)))


def remove_person(request, *args, **kwargs):
    if request.POST:
        registration = Attendance.objects.filter(session_id=kwargs['session_id']).filter(person_id=kwargs['person_id'])
        print(registration)
        registration.delete()

    return HttpResponseRedirect(reverse('TUTRReg:attendance', args=(kwargs['session_id'],)))


def add_class_event(request, *args, **kwargs):
    if request.POST:
        event = Event.objects.filter(pk=kwargs['event_id']).first()
        cls = Class.objects.filter(pk=kwargs['class_id']).first()
        session = Session.objects.create(event_id=event, class_id=cls)
        session.save()

    return HttpResponseRedirect(reverse('TUTRReg:event_detail', args=(kwargs['event_id'],)))


def remove_class(request, *args, **kwargs):
    if request.POST:
        session = Session.objects.filter(pk=kwargs['session_id'])
        session.delete()

    return HttpResponseRedirect(reverse('TUTRReg:event_detail', args=(kwargs['event_id'],)))


def attendance(request, *args, **kwargs):
    if request.POST:
        formset = AttendanceFormSet(session_id=kwargs['session_id'], data=request.POST)
        if formset.is_valid():
            formset.save()
    else:
        formset = AttendanceFormSet(session_id=kwargs['session_id'])
        context = {'formset': formset, 'session_id': kwargs['session_id'], 'class_id': kwargs['class_id']}
    return render(request, 'TUTRReg/attendance.html', context=context)


@login_required()
def landing(request):
    context = {'student': '',
               'dean': None,
               'governor': None,
               'registrar': None}
    user = get_object_or_404(User, pk=request.user.pk)
    if user.groups.filter(name__in=['Dean']).exists():
        context['dean'] = Class.objects.filter(approved=False).all()
    elif user.groups.filter(name__in=['Governor']).exists():
        data = Attendance.objects.values('person_id', 'session_id__class_id__course_id__major_id'
                                         ).exclude(attended=False).exclude(passed=False
                                                                           ).annotate(Sum('session_id__class_id__course_id__credits'))
        context['governor'] = data
    elif user.groups.filter(name__in=['Registrar']).exists():
        context['registrar'] = Event.objects.filter(approved=False)
    else:
        context['student'] = Attendance.objects.filter(person_id=user.person_id
                                                       ).exclude(passed=False).exclude(attended=False).all()
    return render(request, "TUTRReg/landing.html", context)


class CreateEventView(LoginRequiredMixin, generic.CreateView):
    template_name = 'TUTRReg/new_event.html'
    form_class = EventForm
    login_url = '/accounts/login/'
    redirect_field_name = ''

    def form_valid(self, form):
        event = form.save(commit=False)
        event.approved = 0
        event.closed = 0
        event.save()
        return super().form_valid(form)


class UpdateEventView(LoginRequiredMixin, generic.UpdateView):
    model = Event
    template_name = 'TUTRReg/edit_event.html'
    form_class = EventForm
    login_url = '/accounts/login/'
    redirect_field_name = ''

    def form_valid(self, form):
        event = form.save(commit=False)
        event.approved = 0
        event.closed = 0
        event.save()
        return super().form_valid(form)


class CreateClassView(LoginRequiredMixin, generic.CreateView):
    template_name = 'TUTRReg/edit_class.html'
    form_class = ClassForm
    login_url = '/accounts/login/'
    success_url = '/sessions/'

    def form_valid(self, form):
        cls = form.save(commit=False)
        cls.approved = 0
        cls.save()
        return super().form_valid(form)


class UpdateClassView(LoginRequiredMixin, generic.UpdateView):
    model = Class
    template_name = 'TUTRReg/edit_class.html'
    form_class = ClassForm
    login_url = '/accounts/login/'
    redirect_field_name = ''

    def form_valid(self, form):
        cls = form.save(commit=False)
        cls.approved = 0
        cls.save()
        return super().form_valid(form)


class CreatePersonView(LoginRequiredMixin, generic.CreateView):
    template_name = 'TUTRReg/edit_person.html'
    form_class = PersonForm
    login_url = '/accounts/login/'
    success_url = '/sessions/'

    def form_valid(self, form):
        person = form.save(commit=False)
        person.active = 1
        person.save()
        return super().form_valid(form)


class UpdatePersonView(LoginRequiredMixin, generic.UpdateView):
    model = Person
    template_name = 'TUTRReg/edit_person.html'
    form_class = PersonForm
    login_url = '/accounts/login/'
    redirect_field_name = ''

    def form_valid(self, form):

        return super().form_valid(form)


class SessionView(generic.ListView):
    model = Event
    template_name = 'TUTRReg/sessions.html'
    context_object_name = 'EventList'

    def get_context_data(self, *, object_list=None, **kwargs):
        one_year_ago = timezone.now() - timezone.timedelta(days=(365 * 4))
        context = super(SessionView, self).get_context_data(**kwargs)
        context['past_events'] = Event.objects.filter(start_date__gte=one_year_ago, start_date__lte=timezone.now()).order_by('start_date')
        context['future_events'] = Event.objects.filter(start_date__gte=timezone.now()).order_by('start_date')
        return context


class EventDetail(generic.DetailView):
    model = Event
    template_name = 'TUTRReg/event.html'
    context_object_name = 'EventDetailList'

    def get_context_data(self, **kwargs):
        context = super(EventDetail, self).get_context_data(**kwargs)
        context['session'] = Session.objects.filter(event_id=self.kwargs['pk']).all()
        end_date = Event.objects.filter(pk=self.kwargs['pk']).values('end_date').first()['end_date']
        context['open'] = end_date >= timezone.now().date()
        return context


class ClassDetail(generic.DetailView):
    model = Class
    template_name = 'TUTRReg/class.html'
    context_object_name = 'ClassDetails'

    def get_context_data(self, **kwargs):
        context = super(ClassDetail, self).get_context_data(**kwargs)
        return context


class EventClassDetail(generic.DetailView):
    model = Class
    template_name = 'TUTRReg/event_class_detail.html'
    context_object_name = 'EventClassDetails'

    def get_context_data(self, **kwargs):
        context = super(EventClassDetail, self).get_context_data(**kwargs)
        context['session_id'] = self.kwargs['session_id']
        context['class_id'] = self.kwargs['pk']
        return context


class CourseList(LoginRequiredMixin, generic.ListView):
    model = Course
    template_name = 'TUTRReg/course.html'
    context_object_name = 'CourseList'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(CourseList, self).get_context_data(**kwargs)
        context['courses'] = Course.objects.all()


class CourseDetail(LoginRequiredMixin, generic.DetailView):
    model = Course
    template_name = 'TUTRReg/course.html'
    context_object_name = 'CourseDetails'

    def get_context_data(self, **kwargs):
        context = super(CourseDetail, self).get_context_data(**kwargs)
        context['class_list'] = Class.objects.filter(course_id=self.kwargs['pk'])
        return context


class AddClassView(LoginRequiredMixin, generic.ListView):
    template_name = 'TUTRReg/add_class.html'
    login_url = '/accounts/login/'
    redirect_field_name = ''
    paginate_by = 100

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(AddClassView, self).get_context_data(**kwargs)
        context['event_id'] = self.kwargs['event_id']
        context['event'] = Event.objects.filter(pk=self.kwargs['event_id']).first()
        return context

    def get_queryset(self, *args, **kwargs):
        query = self.request.GET.get('class_search')
        if query is None:
            object_list = Class.objects.all()
        else:
            object_list = Class.objects.filter(Q(class_name__icontains=query))
        return object_list


class AddPersonView(LoginRequiredMixin, generic.ListView):
    template_name = 'TUTRReg/add_person.html'
    login_url = '/accounts/login/'
    redirect_field_name = ''
    paginate_by = 100

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(AddPersonView, self).get_context_data(**kwargs)
        context['session_id'] = self.kwargs['session_id']
        context['session'] = Session.objects.filter(pk=self.kwargs['session_id']).first()
        return context

    def get_queryset(self, *args, **kwargs):
        query = self.request.GET.get('person_search')
        if query is None:
            object_list = Person.objects.all()
        else:
            object_list = Person.objects.filter(Q(first_name__icontains=query) |
                                                Q(last_name__icontains=query) |
                                                Q(sca_name__icontains=query))
        return object_list


class UpdateCourseView(LoginRequiredMixin, generic.UpdateView):
    template_name = ''
    login_url = '/accounts/login'
    redirect_field_name = ''

    def get_context_data(self, **kwargs):
        context = super(UpdateCourseView, self).get_context_data(**kwargs)
        context['course_id'] = self.kwargs['course_id']
        context['course'] = Course.objects.filter(pk=context['course_id']).first()


class DegreeList(LoginRequiredMixin, generic.ListView):
    model = Degree
    template_name = 'TUTRReg/degree_list.html'
    context_object_name = 'DegreeList'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DegreeList, self).get_context_data(**kwargs)
        context['degrees'] = Degree.objects.all()
        return context


class DegreeDetail(LoginRequiredMixin, generic.DetailView):
    model = Degree
    template_name = 'TUTRReg/degree.html'
    context_object_name = 'DegreeDetails'

    def get_context_data(self, **kwargs):
        context = super(DegreeDetail, self).get_context_data(**kwargs)
        context['degree'] = Degree.objects.filter(pk=kwargs['pk']).first()
        context['majors'] = Major.objects.filter(degree_cd_id=kwargs['pk']).all()
        return context


class MajorList(LoginRequiredMixin, generic.ListView):
    model = Major
    template_name = 'TUTRReg/major_list.html'
    context_object_name = 'MajorList'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(MajorList, self).get_context_data(**kwargs)
        context['degrees'] = Major.objects.all()
        return context


class MajorDetail(LoginRequiredMixin, generic.DetailView):
    model = Major
    template_name = 'TUTRReg/major.html'
    context_object_name = 'MajorDetails'

    def get_context_data(self, **kwargs):
        context = super(MajorDetail, self).get_context_data(**kwargs)
        context['degree'] = Major.objects.filter(pk=kwargs['pk']).first()
        context['majors'] = Course.objects.filter(major_id=kwargs['pk']).all()
        return context


class AttendanceView(generic.FormView):
    model = Session
    form_class = AttendanceForm
    template_name = 'TUTRReg/attendance.html'

    def get_form(self, form_class=None):
        form = super(AttendanceView, self).get_form(form_class)
        form_data = Session.objects.filter(pk=self.kwargs['pk']).first()
        form.fields['event_id'].initial = form_data.event_id_id
        form.fields['class_id'].initial = form_data.class_id_id
        form.fields['start_time'].initial = form_data.start_time
        form.fields['end_time'].initial = form_data.end_time
        return form

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(AttendanceView, self).get_context_data(**kwargs)
        context['session_id'] = self.kwargs['pk']
        student_data = Attendance.objects.filter(session_id=self.kwargs['pk']).all()
        instance = Session.objects.filter(pk=self.kwargs['pk']).first()
        students = []
        for row in student_data:
            students.append({
                'session_id': row.session_id,
                'person_id': row.person_id,
                'attended': row.attended,
                'passed': row.passed
            })
        if self.request.POST:
            context['students'] = AttendanceFormSet(self.request.POST, instance=instance)
        else:
            context['students'] = AttendanceFormSet(initial=students, instance=instance)
            context['students'].extra = len(students)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        students = context['students']
        form = context['form']
        if form.is_valid():
            instance = form.save(commit=False)
            instance.pk = Session.objects.filter(pk=self.kwargs['pk']).first().pk
            instance.save()

            for student in students:
                if student.is_valid():
                    student_instance = student.save(commit=False)
                    student_instance.save()
                else:
                    print(student.errors)

        return super().form_valid(form)

    def get_success_url(self):
        event = Session.objects.filter(pk=self.kwargs['pk']).first().event_id
        return reverse('TUTRReg:event_detail', kwargs={'pk': event.pk})


