from django.db import models
from django.utils import timezone


# treo.stregsystem.templatetags stregsystem_extras : money
def money(value):
    if value is None:
        value = 0
    return "{0:.2f}".format(value / 100.0)


def price_display(value):
    return money(value) + " kr."


def active_str(a):
    if a:
        return "+"
    else:
        return "-"


# Errors
class StregForbudError(Exception):
    pass


# Create your models here.

# So we have two "basic" operations to do with money
# we can take money from a user and we can give them money
# the class names here are written from the perspective of
# the user.
# A monetary transaction, not a database transaction
class MoneyTransaction(object):
    def __init__(self, amount=0):
        self.amount = amount

    def add(self, change):
        """
        Add to the amount this transaction is for
        """
        self.amount += change

    def change(self):
        raise NotImplementedError

    def __eq__(self, other):
        """
        The equality of two transactions is based on the effect
        to the users balance
        """
        return self.change() == other.change()


class PayTransaction(MoneyTransaction):
    # The change to the users account
    # Negative because the user is losing money
    def change(self):
        """
        Returns the change to the users account
        caused by fulfilling this transaction
        """
        return -self.amount


class GetTransaction(MoneyTransaction):
    # The change to the users account
    def change(self):
        """
        Returns the change to the users account
        caused by fulfilling this transaction
        """
        return self.amount


class Member(models.Model):  # id automatisk...
    GENDER_CHOICES = (
        ('U', 'Unknown'),
        ('M', 'Male'),
        ('F', 'Female'),
    )
    active = models.BooleanField(default=True)
    username = models.CharField(max_length=16)
    year = models.CharField(max_length=4)  # "dato" inkluderer maaned/dag...
    firstname = models.CharField(max_length=20)  # for 'firstname'
    lastname = models.CharField(max_length=30)  # for 'lastname'
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    email = models.EmailField(blank=True)
    want_spam = models.BooleanField(default=True)  # oensker vedkommende fember mails?
    balance = models.IntegerField(default=0)  # hvor mange oerer vedkommende har til gode
    undo_count = models.IntegerField(default=0)  # for 'undos' i alt
    notes = models.TextField(blank=True)

    stregforbud_override = False

    def balance_display(self):
        return money(self.balance) + " kr."

    balance_display.short_description = "Balance"
    balance_display.admin_order_field = 'balance'

    def __unicode__(self):
        return self.username + active_str(self.active) + ": " + self.email + " " + money(self.balance)

    # XXX - virker ikke
    #    def get_absolute_url(self):
    #        return "/stregsystem/1/user/%i/" % self.id

    def make_payment(self, amount):
        """
        Should only be called by the Payment class.

        >>> jokke = Member.objects.create(username="jokke", firstname="Joakim", lastname="Byg", email="treo@cs.aau.dk", year=2007)
        >>> jokke.balance
        0
        >>> jokke.make_payment(100)
        >>> jokke.balance
        100
        """
        self.balance = self.balance + amount

    def fulfill(self, transaction):
        """
        Fulfill the transaction
        """
        if not self.can_fulfill(transaction):
            raise StregForbudError
        self.balance += transaction.change()

    def rollback(self, transaction):
        """
        Rollback transaction
        """
        self.balance -= transaction.change()

    def can_fulfill(self, transaction):
        """
        Can the member fulfill the transaction
        """

        if self.balance + transaction.change() < 0:
            return False
        return True

        #    def clear_undo_count(self):
        #        from django.db import connection
        #        cursor = connection.cursor()
        #        cursor.execute("UPDATE stregsystem_member SET undo_count = 0 WHERE id = %s", [self.id])
        #        return

    def has_stregforbud(self, buy=0):
        # hyttetur, julefrokost, paaskefrokost override
        # if buy == 30000 or buy == 27000 or buy == 25000 or buy == 17500 or buy == 1500 or buy == 3500 or buy == 10000 or buy == 33300 or buy == 22200:
        #    return False
        if Member.stregforbud_override:
            return False

        return self.balance - buy < 0

    def calculate_alcohol_promille(self):
        # Disabled:
        # return False
        from datetime import timedelta
        # formodet draenet vaegt paa en gennemsnitsdatalog
        weight = 80.0
        # Vi burde flytte det her til databasen, saa kan treoen lave noget ;)
        drinks_in_product = {13: 1.24, 14: 1.0, 29: 1.0, 42: 1.72, 47: 1.52, 54: 1.24, 65: 1.5, 66: 1.5,
                             1773: 1.0, 1776: 1.52, 1777: 1.52, 1779: 2.0, 1780: 2.58, 1783: 1.0, 1793: 1.0, 1794: 0.96,
                             22: 7.0, 23: 7.0, 41: 19.14, 53: 9.22, 63: 1.0, 64: 7.0, 1767: 1.02, 1769: 1.0, 1770: 2.0,
                             1802: 2.0, 1807: 6.6, 1808: 7.5, 1809: 8.3}

        now = timezone.now()
        delta = now - timedelta(hours=12)
        alcohol_sales = Sale.objects.filter(member_id=self.id, timestamp__gt=delta,
                                            product__in=list(drinks_in_product.keys())).order_by('timestamp')
        drinks = 0.0

        if self.gender == 'M':
            drinks_pr_hour = 0.01250 * weight
        elif self.gender == 'F':
            drinks_pr_hour = 0.00833 * weight
        else:
            # tilfaeldigt gennemsnit for ukendt koen
            drinks_pr_hour = 0.01042 * weight

        if (len(alcohol_sales) > 0):
            last_time_frame = alcohol_sales[0].timestamp
            for sale in alcohol_sales:
                current_time_frame = sale.timestamp
                drinks = max(0.0, drinks - (current_time_frame - last_time_frame).seconds / 3600.0 * drinks_pr_hour)
                drinks = drinks + drinks_in_product[sale.product_id]
                last_time_frame = current_time_frame
            drinks = max(0.0, drinks - (now - last_time_frame).seconds / 3600.0 * drinks_pr_hour)

        # Tihi:
        drunken_bastards = {
            2219: 42.0,  # mbogh
            2124: -1.5,  # mchro
            2113: 42.0,  # kyrke
            2024: 31.5,  # jbr
            2414: 5440,  # kkkas
        }

        if self.gender == 'M':
            consume_percent = 0.68
        elif self.gender == 'F':
            consume_percent = 0.55
        else:
            consume_percent = 0.615

        promille = 12.0 * drinks / (consume_percent * weight)
        promille = promille + drunken_bastards.get(self.id, 0.0)
        return str(round(promille, 2))


class Payment(models.Model):  # id automatisk...
    member = models.ForeignKey(Member)
    timestamp = models.DateTimeField(auto_now_add=True)
    amount = models.IntegerField()  # penge, oere...

    def amount_display(self):
        return money(self.amount) + " kr."

    amount_display.short_description = "Amount"
    # XXX - django bug - kan ikke vaelge mellem desc og asc i admin, som ved normalt felt
    amount_display.admin_order_field = '-amount'

    def __unicode__(self):
        return self.member.username + " " + str(self.timestamp) + ": " + money(self.amount)

    def save(self, *args, **kwargs):
        if self.id:
            return  # update -- should not be allowed
        else:
            # TODO: Make atomic
            self.member.make_payment(self.amount)
            super(Payment, self).save(*args, **kwargs)
            self.member.save()

    def delete(self, *args, **kwargs):
        if self.id:
            # TODO: Make atomic
            self.member.make_payment(-self.amount)
            super(Payment, self).delete(*args, **kwargs)
            self.member.save()
        else:
            super(Payment, self).delete(*args, **kwargs)


class Product(models.Model):  # id automatisk...
    name = models.CharField(max_length=32)
    price = models.IntegerField()  # penge, oere...
    active = models.BooleanField()
    deactivate_date = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return active_str(self.active) + " " + self.name + " (" + money(self.price) + ")"

    def save(self, *args, **kwargs):
        price_changed = True
        if self.id:
            try:
                oldprice = self.old_prices.order_by('-changed_on')[0:1].get()
                price_changed = oldprice != self.price
            except OldPrice.DoesNotExist:  # der findes varer hvor der ikke er nogen "tidligere priser"
                pass
        super(Product, self).save(*args, **kwargs)
        if price_changed:
            OldPrice.objects.create(product=self, price=self.price)


class OldPrice(models.Model):  # gamle priser, skal huskes; til regnskab/statistik?
    product = models.ForeignKey(Product, related_name='old_prices')
    price = models.IntegerField()  # penge, oere...
    changed_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.product.name + ": " + money(self.price) + " (" + str(self.changed_on) + ")"


# XXX
class Room(models.Model):
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name


class Sale(models.Model):
    member = models.ForeignKey(Member)
    product = models.ForeignKey(Product)
    room = models.ForeignKey(Room, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    price = models.IntegerField()

    def price_display(self):
        return money(self.price) + " kr."

    price_display.short_description = "Price"
    # XXX - django bug - kan ikke vaelge mellem desc og asc i admin, som ved normalt felt
    price_display.admin_order_field = 'price'

    def __unicode__(self):
        return self.member.username + " " + self.product.name + " (" + money(self.price) + ") " + str(self.timestamp)

    def save(self, *args, **kwargs):
        if self.id:
            raise RuntimeError("Updates of sales are not allowed")
        super(Sale, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.id:
            super(Sale, self).delete(*args, **kwargs)
        else:
            raise RuntimeError("You can't delete a sale that hasn't happened")


# XXX
class News(models.Model):
    title = models.CharField(max_length=40)
    text = models.TextField()
    pub_date = models.DateTimeField()
    stop_date = models.DateTimeField()

    class Meta:
        verbose_name_plural = "News"

    def __unicode__(self):
        return self.title + " -- " + str(self.pub_date)
