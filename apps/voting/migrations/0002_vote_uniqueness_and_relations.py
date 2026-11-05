# Generated for Entrega 3: Model de Votos e Integridad por Usuario, Categoria y Edicion
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='vote',
            name='category',
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='votes',
                to='voting.category',
                verbose_name='Contest Category'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vote',
            name='edition',
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='votes',
                to='voting.edition',
                verbose_name='Festival Edition'
            ),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name='vote',
            constraint=models.UniqueConstraint(
                fields=('user', 'edition', 'category'),
                name='unique_vote_per_user_category_edition'
            ),
        ),
    ]
