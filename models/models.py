# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from datetime import timedelta


class Course(models.Model):
    _name = 'openacademy.course'

    name = fields.Char(string="Title", required=True)
    description = fields.Text()

    responsible_id = fields.Manny2one(
        'res.users',
        ondelete='set null',
        string="Responsible",
        index=True)


class Session(models.Model):
    _name = 'openacademy.session'

    name = fields.Char(required=True)
    start_date = fields.Date()
    duration = fields.Float(digits=(6, 2), help="Duration in days")
    seats = fields.Integer(string="Number of seats")
    active = fields.Boolean(default=True)
    instructor_id = fields.Many2one(
        'res.partner', string="Instructor", domain=[
            '|', ('instructor', '"', True)])

    instructor_id = fields.Many2one('res.partner', string="Instructor")
    course_id = fields.Many2one(
        'openacademy.course',
        ondelete='cascade',
        string="Course",
        required=True)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")
    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')
    end_date = fields.Date(
        string="End Date",
        store=True,
        compute="_get_end_date",
        inverse='_set_end_date')

    @api.multi
    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
            [('name', '=like', u"Copy of {}%".format(self.name))])
        if not copied_count:
            new_name = u"Copy of {}".format(self.name)
        else:
            new_name = u"Copy of {} ({})".format(self.name, copied_count)

        default['name'] = new_name
        return super(Course, self).copy(default)

    @api.depends('start_date', 'duration')
    def _taken_seats(self):
        for r in self:
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue
            start = fields.Datetime.from_string(r.start_date)
            duration = timedelta(days=r.duration, seconds=-1)
            r.end_date = start + duration

    def _set_end_date(self):
        for r in self:
            if not(r.start_date and r.end_date):
                continue

            start_date = fields.Datetime.from_string(r.start_date)
            end_date = fields.Datetime.from_string(r.end_date)
            r.duration = (end_date - start_date).days + 1

    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': "Incorrect 'seats' value",
                    'message': "The number of available seats may not be negative",
                },
            }
            if self.seats < len(self.attendee_ids):
                return {
                    'warning': {
                        'title': "Too many attendees",
                        'message': "Increase seats or remove excess attendees",
                    },
                }

    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendes(self):
        for r in self:
            if r.instructor_id and r.instructor_id in r.attendee_ids:
                raise exceptions.ValidationError(
                    "A session's instructor can't be an attendee")
